#!/usr/bin/env python
"""
Description: Script for pre-processing S1 imagery.
             Due to compatibility issues between the download
             library and the processing library (snappy), we
             need to
Original Author: leigh.tyers@curtin.edu.au
Creation Date: 2023-01-13

Modified by Calvin Pang (calvin.pang@curtin.edu.au)
Modified Date: 2023-03-13
"""
import logging
import os
import re
import sys
from pathlib import Path

import getpass
from osgeo import ogr, osr
from eodag import EODataAccessGateway, setup_logging
from eodag.utils.exceptions import AuthenticationError

from config import log_fname, work_dir, search_criteria
from src.downloader_config import download_from_thredds, del_intermediate
from src.downloader_utils import download_product_thredds

Path(log_fname).parent.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(log_fname), logging.StreamHandler(sys.stdout)],
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def write_shapefile(polygon, fpath="data/search_polygon.shp", crs_num=4326):
    """
    Writes an ESRI shapefile from a shapely polygon using osgeo.

    Parameters
    ----------
    polygon: shapely.geometry.Polygon
        A shapely polygon to be written to shapefile.
    fpath: str, optional
        The file path to save the shapefile to.
        Default is "data/search_polygon.shp".
    crs_num: int, optional
        The Coordinate Reference System (CRS) number, default is 4326

    Returns
    -------
    None
    """
    crs_num = int(crs_num)

    # Create a polygon from a ring (which we can assign points to)
    ring = None
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in polygon.boundary.coords:
        ring.AddPoint(coord[0], coord[1])
        lastPoint = [coord[0], coord[1]]

    poly = ogr.Geometry(ogr.wkbPolygon)

    poly.AddGeometry(ring)

    # Set up the shapefile driver
    driver = ogr.GetDriverByName("ESRI Shapefile")

    # create the data source
    Path(fpath).parent.mkdir(exist_ok=True)
    ds = driver.CreateDataSource(fpath)

    # create the spatial reference system, WGS84
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(crs_num)

    # create one layer self
    layer = ds.CreateLayer("polygon", srs, ogr.wkbPolygon)

    # Add an ID field
    idField = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(idField)

    # Create the feature and set values
    featureDefn = layer.GetLayerDefn()
    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(poly)
    feature.SetField("id", 1)
    layer.CreateFeature(feature)

    feature = None

    # Save and close DataSource. This HAS to be done to avoid memory leaks
    ds = None
    return


def check_file_processed(
    fname, final_data_path="./data/data_processed/", zip_file_given=False
):
    """
    Check if a file has already been processed.

    Parameters
    ----------
    fname : str
        The name of the file to check
    final_data_path: str, optional
        The path to the directory where processed files are stored.
        Default is "./data/data_processed/".
    zip_file_given: bool, optional
        Whether the input file is a zip file.
        Default is False.

    Returns
    -------
    bool
        True if the file has already been processed, else False.

    """
    fname = Path(fname).name
    if zip_file_given:
        fname = re.sub("(.zip)$", "_processed.tif", fname)
    meta_dir = Path(final_data_path, ".processed")
    file_suffix = ".done"
    meta_file_exists = Path(meta_dir, fname + file_suffix).is_file()
    og_file_exists = Path(final_data_path, fname).is_file()
    return bool(meta_file_exists and og_file_exists)


def create_proc_metadata(
    fname, final_data_path="./data/data_processed/", zip_file_given=False
):
    """
    Creates metadata that the file has been processed for future use in '.processed'.

    Parameters
    ----------
    fname : str
        The name of the file to create metadata for
    final_data_path: str, optional
        The path to the directory where processed files are stored.
        Default is "./data/data_processed/".
    zip_file_given: bool, optional
        Whether the input file is a zip file.
        Default is False.

    Returns
    -------
    None

    """
    fname = Path(fname).name
    if zip_file_given:
        fname = re.sub("(.zip)$", "_processed.tif", fname)
    meta_dir = Path(final_data_path, ".processed")
    Path(meta_dir, f"{fname}.done").touch()
    return


def download_and_process_product(
    product, data_directory, del_intermediate=True, download_from_thredds=False
):
    """
    Downloads and processes a Sentinel-1 product from an EODAG product

    Parameters
    ----------
    product : eodag.api.product.EOProduct
        A queried Sentinel-1 product object from EODAG.
    data_directory : str
        The directory where the product should be downloaded and processed.
    del_intermediate : bool
        Whether to delete intermediate files after processing. Default is True.
    download_from_thredds : bool
        Whether to download the product from THREDDS instead of from EODAG. Default is False.

    Returns
    -------
    None
    """
    raw_data_path = Path(data_directory, 'data_raw')
    final_data_path = Path(data_directory, "data_processed")
    # --------------------------------
    # Download file
    log.info("-" * 40)
    log.info(f"Starting download for product {product.properties['title']}")
    # NCI's THREDDS dataserver is a publicly accessible data repository
    # It does not need authentication. The top-level repo is here:
    # https://dapds00.nci.org.au/thredds/catalog.html
    if download_from_thredds:
        fname = download_product_thredds(product, raw_data_path)
    else:
        fname = product.download(extract=False)

    fpath_proc = Path(final_data_path, f'{(Path(fname).name)[:-4]}"_processed.tif')
    cog_fname = re.sub("(.tif)$", "_cog.tif", str(fpath_proc))

    if check_file_processed(cog_fname, final_data_path, zip_file_given=False):
        log.info(f"Skipping processing {cog_fname} as it already exists.")
        return
    return


def run_all(download_from_thredds, data_directory, search_criteria, del_intermediate):
    """
    Function to be called from main.
    It retrieves products from EODAG with given search criteria and bounds,
    downloads and processes the products using eodag API and other helper functions.

    Parameters
    ----------
    download_from_thredds (bool)
        flag to download the products from thredds or not.
    data_directory (str)
        path to the directory where the downloaded products will be saved
    bounds (Tuple)
        tuple of (min_lon,min_lat,max_lon,max_lat) for spatial search
    search_criteria (Dict)
        dictionary of key-value pairs for filtering the search results
    del_intermediate (bool)
        flag to delete intermediate files (eg the raw output of snappy when computed the cog)

    Returns:
    ----------
    None
    """
    raw_data_path = Path(data_directory, 'data_raw')
    raw_data_path.mkdir(exist_ok=True)

    os.environ["EODAG__SARA__DOWNLOAD__OUTPUTS_PREFIX"] = str(raw_data_path)

    if not download_from_thredds:
        os.environ["EODAG__SARA__AUTH__CREDENTIALS__USERNAME"] = input(
            "Please enter your SARA username, then press ENTER (not SHIFT+ENTER)"
        )
        os.environ["EODAG__SARA__AUTH__CREDENTIALS__PASSWORD"] = getpass.getpass(
            "Enter your password for SARA then press enter (not SHIFT+ENTER). The password will not be shown. Passwd:"
        )

    setup_logging(verbose=2)

    dag = EODataAccessGateway()

    dag.set_preferred_provider("sara")

    search_products = dag.search_all(
        **search_criteria
    )  # This should log the number of search products

    for product in search_products:
        log.info("=" * 60)
        log.info(f"Now processing file {product.properties['title']}")
        try:
            download_and_process_product(
                product,
                data_directory=data_directory,
                del_intermediate=del_intermediate,
                download_from_thredds=download_from_thredds,
            )
        except AuthenticationError as e:
            log.error("=" * 60)
            log.error("***AUTHENTICATION ERROR***")
            log.error("Authentication provided likely is not correct.")
            log.error("Processing will attempt to continue just")
            log.error("in case files are already present.")
            log.error("If this isnt wanted, CTRL + C out.")
            log.exception("The exception is: ")
            log.error("End of exception")
            log.error("=" * 60)
        except Exception:
            log.error("=" * 60)
            log.exception(
                f"Non exit exception caught. Program will try again in case it was a timeout."
            )
            log.exception("Exception is:")
            log.error("End of exception")
            log.error("=" * 60)
            log.error("Continuing...")


def main():
    log.info(
        "Beggining log for new program run, inserting lines for visual clarity"
        + "\n" * 6
    )
    log.info("New program run:")
    log.info("=" * 60)
    run_all(
        download_from_thredds=download_from_thredds,
        data_directory=work_dir,
        search_criteria=search_criteria,
        del_intermediate=del_intermediate,
    )


if __name__ == "__main__":
    # Load config & setup
    main()
