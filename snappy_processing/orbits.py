#!/bin/env/python


import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from os.path import join, basename, isfile
import requests
import re


logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def get_orbit_files(product_name: str, aux_path: Path) -> None:
    """Makes sure an orbitfile is in the correct location

    Parameters
    ----------
    product_name
        product name from SNAP `product.name` method
    orbit_path
        auxillary data path to look and store data to

    """
    orbit_path = Path(aux_path) / "orbits"

    # Try to query orbits
    urls = query_orbit(product_name)
    # Download URLS as needed
    download_urls(urls=urls, out_dir=orbit_path)
    # Move products across to where snap is looking for them. They should be relatively small so no issue with copy over mv
    old_product_paths = get_old_orbit_data_paths(product_name, orbit_path=orbit_path)
    if len(old_product_paths) == 0:
        log.error("No orbit files found after download attempt")
        return
    new_product_paths = get_new_orbit_data_paths(product_name, orbit_path=orbit_path)
    for old_path, new_path in zip(old_product_paths, new_product_paths):
        Path(new_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(old_path, new_path)
        except shutil.SameFileError:
            pass
    return


def get_old_orbit_data_paths(product_name: str, orbit_path: str) -> str:
    """Gets a product path from a S1A file product_name that is in the data directory

    Paremters
    ---------
    product_name
        the result from the SNAP product.name method, similar to a filename
    orbit_path : optional
        the path to the auxilary file directory (containing an 'orbits' folder)
    """
    # Exampe product_name is S1A_IW_GRDH_1SDV_20230131T104608_20230131T104643_047026_05A40B_7F91
    # S1A_IW_GRDH_1SDV_20230131T104608_20230131T104643_047026_05A40B_7F91_processed.tif
    # S1A_IW_GRDH_1SDV_20230131T104608_20230131T104643_047026_05A40B_7F91.zip
    # example orbitfile is S1A_OPER_AUX_POEORB_OPOD_20230220T080804_V20230130T225942_20230201T005942.EOF.zip

    intial_orbits_dir = Path(orbit_path)
    intial_orbits_fpaths = list(intial_orbits_dir.glob("S1*.EOF.zip"))

    # transform orbit filenames into date ranges
    def get_date(name: str, key: int = 6) -> datetime:
        date_str = name.split("_")[key].strip("V").replace(".EOF.zip", "")
        date = datetime.strptime(date_str, "%Y%m%dT%H%M%S")
        return date

    orbit_dates = {
        fpath: [get_date(fpath.name, key=6), get_date(fpath.name, key=7)]
        for fpath in intial_orbits_fpaths
    }
    log.info(f"{len(orbit_dates)} orbit dates found in dir: {intial_orbits_dir}")

    # find orbit files that encompass the product's date

    matching_files = []
    min_prod_date, max_prod_date = [get_date(product_name, key=4), get_date(product_name, key=5)]
    for fpath, (min_orbit_date, max_orbit_date) in orbit_dates.items():
        date_intersection = (min_prod_date >= min_orbit_date) and (min_prod_date <= max_orbit_date)
        date_intersection |= (max_prod_date >= min_orbit_date) and (max_prod_date <= max_orbit_date)
        if date_intersection:
            matching_files.append(fpath)
    return matching_files


def get_new_orbit_data_paths(product_name: str, orbit_path: Path) -> str:
    """Gets the location an aux file needs to be to be understood by snap"""
    filenames = [
        Path(file).name for file in get_old_orbit_data_paths(product_name, orbit_path=orbit_path)
    ]
    product_name_components = product_name.split("_")
    new_product_path = Path("~/.snap/auxdata/Orbits/Sentinel-1").expanduser()
    data_paths = []
    for orbit_type in ["POEORB", "RESORB"]:
        sat = product_name_components[0]
        year_str = product_name_components[4][:4]
        month_str = product_name_components[4][4:6]
        data_paths += [
            (new_product_path / orbit_type / sat / year_str / month_str / filename).as_posix()
            for filename in filenames
        ]
    return data_paths


def query_orbit(product_name: str) -> list:
    """
    Queries a S1 orbit for parameters from product_name and retrieves a download URL from step.esa.int/auxdata

    Parameters
    ----------
    product_name
        the product name from the SNAP `product.name` method for a S1 file
    """
    product_name_components = product_name.split("_")
    sat = product_name_components[0]  # TODO: to be used for filtering S1A/S1C

    date_fmt_in = "%Y%m%dT%H%M%S"
    date_fmt_Z = "%Y-%m-%dT%H:%M:%SZ"
    date_fmt_Z2 = "%Y-%m-%dT%H:%M:%S.%f"
    # Orbitfiles have a duration of ~1 day 2 hours, + an hour to buffer the search
    satfile_duration = timedelta(days=1, hours=3)
    startDate = datetime.strptime(product_name_components[4], date_fmt_in) - satfile_duration
    completionDate = datetime.strptime(product_name_components[5], date_fmt_in) + satfile_duration
    # Hardcoding the API string for now. Really
    api_url = r"https://catalogue.dataspace.copernicus.eu/resto/api/collections/search.json?"

    orbit_urls = []
    orbit_types = ["POEORB", "RESORB"]
    for orbit_type in orbit_types:
        query_str = "&".join(
            [
                f"platform=SENTINEL-1",
                f"productType=AUX_{orbit_type}",
                f"startDate={startDate.strftime(date_fmt_Z)}",
                f"completionDate={completionDate.strftime(date_fmt_Z)}",
            ]
        )
        query_url = api_url + query_str
        r = requests.get(query_url)
        # not going to bother iterating through pages; we should only get 1-2 results, with 20 max per page
        # Currently the 'exactCount' and 'totalResults' responses seems broken, stuck at 0/None, making this more difficult too
        r_data = r.json()
        # Parse data to get info needed for the url:
        # https://step.esa.int/auxdata/orbits/Sentinel-1/RESORB/S1A/2024/07/
        # S1A_OPER_AUX_RESORB_OPOD_20240701T035859_V20240701T000248_20240701T032018.EOF.zip
        # productIdentifier example:
        # /eodata/Sentinel-1/AUX/AUX_POEORB/2023/01/30/S1A_OPER_AUX_POEORB_OPOD_20230220T080804_V20230130T225942_20230201T005942.EOF'
        for orbit_features in r_data["features"]:
            orbit_data = orbit_features["properties"]
            url_info = {
                "fname": orbit_data["productIdentifier"].split("/")[-1] + ".zip",
                "sat": orbit_data["title"][:3],  # e.g. S1A
                "orbit": orbit_data["productType"].split("_")[-1],
                "startDate": datetime.strptime(orbit_data["startDate"][:-1], date_fmt_Z2),
            }
            # Now form the url
            base_url = "https://step.esa.int/auxdata/orbits/Sentinel-1"
            orbit_url_suffix = "/".join(
                [
                    url_info["orbit"],
                    url_info["sat"],
                    f'{url_info["startDate"].year}',
                    f'{url_info["startDate"].month:02d}',
                    url_info["fname"],
                ]
            )
            orbit_url = base_url + "/" + orbit_url_suffix
            orbit_urls.append(orbit_url)

    return orbit_urls


def download_urls(urls: list, out_dir: Path) -> None:
    """Downloads files from a list of urls if they dont already exist"""
    out_dir = Path(out_dir)

    log.info(f"Attempting to download {len(urls)} files...")
    for url in urls:
        response = requests.get(url, stream=True)
        new_size = int(response.headers.get("content-length", 0))
        block_size = 8192
        filepath = out_dir / Path(url).name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        # Could check hash from headers['content-digest'] in addition to filesize check
        if filepath.is_file():
            existing_filesize = os.path.getsize(filepath)
            if new_size == existing_filesize:
                log.info(f"File {filepath.as_posix()} exists with same size! skipping")
                continue

        log.info(f"Downloading url: {url}")
        log.info(f"Downloading to: {filepath}")
        with open(filepath, "wb") as file:
            for data in response.iter_content(block_size):
                file.write(data)
    return
