#!/usr/bin/env python
"""
Description: Script for pre-processing S1 imagery.
             Due to compatibility issues between the download
             library and the processing library (snappy), we
             seperate the snappy processing into a docker container.
Original Author: leigh.tyers@curtin.edu.au
Creation Date: 2023-01-13
"""
import logging
import os
import sys
import os
import subprocess
import re
from os.path import join, basename, isfile
from pathlib import Path
import getpass
from subprocess import Popen, PIPE, STDOUT
import shutil
import json

from osgeo import ogr
from osgeo import osr
from eodag import EODataAccessGateway
from eodag import setup_logging
from eodag.utils.exceptions import AuthenticationError
from osgeo import gdal

from main_config import log_fname, data_directory

log_fname = os.path.join(data_directory, log_fname)
log_fname = Path(log_fname).expanduser().resolve().as_posix()
os.makedirs(os.path.dirname(log_fname), exist_ok=True)
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(log_fname), logging.StreamHandler(sys.stdout)],
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

from download_utils import download_product_thredds


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
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
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


def check_file_processed(fname, final_data_path="./data/data_processed/", zip_file_given=False):
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
    fname = basename(fname)
    if zip_file_given:
        fname = re.sub("(.zip)$", "_processed.tif", fname)
    meta_dir = join(final_data_path, ".processed")
    file_suffix = ".done"
    meta_file_exists = isfile(join(meta_dir, fname + file_suffix))
    og_file_exists = isfile(join(final_data_path, fname))
    if meta_file_exists and og_file_exists:
        return True
    return False


def create_proc_metadata(fname, final_data_path="./data/data_processed/", zip_file_given=False):
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

    fname = basename(fname)
    if zip_file_given:
        fname = re.sub("(.zip)$", "_processed.tif", fname)
    meta_dir = join(final_data_path, ".processed")
    Path(join(meta_dir, fname + ".done")).touch()
    return


def docker_is_root():
    """
    Checks if the docker version on linux is a root install (not rootless) via a system call
    """
    try:
        text_output = subprocess.check_output("docker version | grep rootlesskit", shell=True)
    except:
        text_output = None
    is_root = False if (text_output) else True
    return is_root


def check_docker_image_exists(container_name: str = "s1a_proc") -> bool:
    """Checks if a docker image is in the local cache"""
    cmd = 'docker image list --filter "reference=landgate" --format json'
    proc = subprocess.Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    std_out, err = proc.communicate()
    # output is a byte string so we need to decode it
    std_out_split = std_out.decode("utf-8").split("\n")
    images = [json.loads(line) for line in std_out_split if line]
    image_exists = any([image["Repository"] == container_name for image in images])
    log.info(f"Does docker image {container_name} exist: {image_exists}")
    return image_exists


def build_docker_container(container_name: str = "s1a_proc", location: str = "snappy_processing"):
    """Builds a docker container from a location"""
    base_path = sys.path[0]
    location_path_full = Path(base_path) / location
    log.info(f"Building docker container {container_name} from {location_path_full}")
    cmd = f"docker build {location_path_full} -t {container_name}"
    log.info(f"Running cmd '{cmd}'")
    proc = subprocess.Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    with proc.stdout:
        log_subprocess_output(proc.stdout, initial_text="Docker build ouput: ")
    proc.wait()
    return


def form_docker_command(
    run_dir, container_name="s1a_proc", filename=None, file_list=None, **kwargs
):
    """Forms the command to run docker

    See Also
    --------
    run_docker_container : Uses this function
    """
    cmd = f"docker run --rm -v {run_dir}/:/app/data "
    if docker_is_root():
        cmd += " --user $(id -u):$(id -g) "
    cmd += f" {container_name} "

    if file_list:
        cmd += " --filelist 'data/files_to_process.txt'"
        # Santise files and output
        file_list = [os.path.basename(f) for f in file_list]
        with open(join(data_directory, "files_to_process.txt"), "w") as f:
            f.writelines("\n".join(file_list))
    elif filename:
        cmd += f" --filename {filename}"
    else:
        raise ValueError("File_list and filename are not valid.")

    for key, val in kwargs.items():
        if key == "shapefile":
            cmd += f"  --{key} '{join('data', os.path.basename(val))}'"
        else:
            cmd += f"  --{key} '{val}'"

    return cmd


def log_subprocess_output(pipe, initial_text="Docker Output: ") -> None:
    # need to read output as bytes, so encode + concat then decode or a bug printing blank lines occurs. No idea why
    for line in iter(pipe.readline, b""):
        log.info((initial_text.encode() + line.rstrip()).decode())

    return


def run_docker_container(
    filename=None, file_list=None, data_directory="data", config_override=True, **kwargs
) -> None:
    """
    Runs the docker container with appropriate cmdline arguments

    Parameters
    ----------
    filename : str, optional
        The name of the file to be processed, either filename or file_list is required
    file_list : list, optional
        The list of files to be processed, either filename or file_list is required
    data_directory : str, optional
        The directory where the data is located, default is "data"
    config_override : bool, optional
        A flag to indicate if the config file should be overridden, default is False
    **kwargs:
        Additional command line arguments passed to the container

    Returns
    -------
    None

    """

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.info("Beggining logging...")

    run_dir = os.path.abspath(data_directory)

    image_name = "s1a_proc"
    image_exists = check_docker_image_exists(container_name=image_name)
    if not image_exists:
        build_docker_container(container_name=image_name)

    cmd = form_docker_command(
        run_dir=run_dir, container_name=image_name, filename=filename, file_list=file_list, **kwargs
    )
    log.info(f"Docker command is: {cmd}")
    # The docker image needs a local copy of config in the appropriate directory.
    code_dir = os.path.dirname(os.path.realpath(__file__))
    try:
        if (not isfile(join(data_directory, "config.py"))) or config_override:
            os.makedirs(data_directory, exist_ok=True)
            shutil.copy(join(code_dir, "main_config.py"), join(data_directory, "config.py"))
    except shutil.SameFileError:
        pass
    # move shapefile into relevat

    log.info(["-" * 50])
    log.info([f"    Processing file {filename}  "])
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        log_subprocess_output(process.stdout)

    exitcode = process.wait()  # 0 means success
    if not exitcode:
        log.info("    Exitcode 0, docker container success")
    else:
        log.error(f"    Exitcode nonzero for file: {filename}")
        log.error(f"    Exitcode was: {exitcode}")
    return


def reformat_geotif(input_fname, output_fname=None):
    """
    Reformats a geotiff to be a COG with lossless options.

    Parameters
    ----------
    input_fname : str
        The path to the input geotiff file.
    output_fname : str, optional
        The path to the output COG file, by default None.
        If None, will append '_cog.tif' to the input file name.

    Returns
    -------
    str
        The path to the output COG file.
    """

    if output_fname is None:
        output_fname = re.sub("(.tif)$", "_cog.tif", input_fname)
    options = gdal.TranslateOptions(
        format="COG",
        noData=0,
        options=[
            "-co",
            "COMPRESS=LZW",
            "-co",
            "PREDICTOR=2",
            "-co",
            "NUM_THREADS=ALL_CPUS",
        ],
    )
    d = gdal.Translate(output_fname, input_fname, options=options)
    d = None
    return output_fname


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

    raw_data_path = os.path.join(data_directory, "data_raw")
    final_data_path = os.path.join(data_directory, "data_processed")
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

    fpath_proc = join(final_data_path, os.path.basename(fname))[:-4] + "_processed.tif"
    cog_fname = re.sub("(.tif)$", "_cog.tif", fpath_proc)

    if check_file_processed(cog_fname, final_data_path, zip_file_given=False):
        log.info(f"Skipping processing {cog_fname} as it already exists.")
        return

    # --------------------------------
    # Pre-process file
    log.info("-" * 40)
    log.info(f"   Starting snappy processing for product {product.properties['title']}")
    run_docker_container(fname, data_directory=data_directory)

    # --------------------------------
    # reformat file
    log.info("-" * 40)
    log.info(f"   Starting cog reformatting for product {product.properties['title']}")
    if not os.path.isfile(fpath_proc):
        log.error(f" File {fpath_proc} does not exist.")
        return

    reformat_geotif(fpath_proc)
    create_proc_metadata(cog_fname, final_data_path, zip_file_given=False)
    # Clean up
    if del_intermediate:
        try:
            os.remove(fpath_proc)
            os.remove(
                join(data_directory, "data_processed", ".processed", basename(fpath_proc) + ".done")
            )
        except ValueError:
            log.error("@" * 10)
            log.error("Process likely failed at an earlier step, continuing")
            log.error("@" * 10)

    log.info(f"All done for {product.properties['title']}")
    log.info("-" * 20)
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

    raw_data_path = os.path.join(data_directory, "data_raw")
    final_data_path = os.path.join(data_directory, "data_processed")

    # raw_data_path = os.path.join(data_directory, 'data_raw')
    # final_data_path = os.path.join(data_directory, 'data_processed')
    os.makedirs(raw_data_path, exist_ok=True)

    os.environ["EODAG__SARA__DOWNLOAD__OUTPUTS_PREFIX"] = os.path.abspath(raw_data_path)

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
    from main_config import download_from_thredds
    from main_config import data_directory
    from main_config import search_criteria
    from main_config import del_intermediate

    log.info("Beggining log for new program run, inserting lines for visual clarity" + "\n" * 6)
    log.info("New program run:")
    log.info("=" * 60)
    data_directory = Path(data_directory).expanduser().as_posix()
    log.info(f"Data directory is {data_directory}")
    run_all(
        download_from_thredds=download_from_thredds,
        data_directory=data_directory,
        search_criteria=search_criteria,
        del_intermediate=del_intermediate,
    )


if __name__ == "__main__":
    # Load config & setup
    main()
