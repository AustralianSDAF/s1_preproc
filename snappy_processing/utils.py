#!/bin/env/python

# import imp
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from os.path import join, basename, isfile
import requests
import re

# For more information on using the S1TBX (now known as the microwave toolbox, see https://step.esa.int/main/doc/tutorials/)

# For more information on using snappy, see https://senbox.atlassian.net/wiki/spaces/SNAP/pages/19300362/How+to+use+the+SNAP+API+from+Python
from snappy import ProductIO

from snappy import WKTReader
from snappy import HashMap
from snappy import GPF
from shapely import wkt
from shapely.geometry import Polygon
import shapely
import snappy
import shapefile
import pygeoif


logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def pre_checks(
    filename,
    filelist,
    raw_data_path,
    s1tbx_operator_order,
    final_data_path,
    archive_data_path,
    do_archive_data,
    shapefile_subdirectory,
):
    """perform directory structure check

    :return: if return = 0 -> no file to processs | if return = -1 -> Error | else: Success
    :rtype: int
    """
    # TODO: Change returns to exception raises

    # checking paths
    cwd = os.getcwd()
    log.debug("Checking data directories")

    if filename and filelist:
        log.error("Please only give one of filename or filelist")
        return -1
    if not (filename or filelist):
        log.error("Please give at least one of filename or filelist")
        return -1

    if not os.path.exists(os.path.join(cwd, "data/config.py")):
        log.error("could not find config file in data/config.py")
        return -1

    if (not os.path.exists(os.path.join(cwd, raw_data_path))) and (filename is not None):
        log.error(
            "Raw data directory {} does not exist. Terminating execution ...".format(raw_data_path)
        )
        return -1

    # Ensure all have an error operatorName and are dictionaries
    for operation_config in s1tbx_operator_order:
        if not isinstance(operation_config, dict):
            log.error(f"operator config was not a dict! It is of type: {type(operation_config)}")
            return -1
        if "operatorName" not in operation_config:
            log.error(
                "No operator name in operator config found in `s1tbx_operator_order` in config file"
            )
            log.error(f"Other parameters in bad operator_config are {operation_config.items()}")
            return -1
        # make sure Subset operator has the needed parameters
        if operation_config["operatorName"] == "Subset":
            needed_Subset_names = ["polygon", "shapefilePath"]
            names_in_params = any([(name in operation_config) for name in needed_Subset_names])
            if not names_in_params:
                return -1
        # Make sure a subset shapefile exists
        if "shapefilePath" in operation_config:
            shapefile_dir = Path(shapefile_subdirectory)
            shapefile_path = shapefile_dir / Path(operation_config["shapefilePath"]).name
            if not shapefile_path.is_file():
                log.error(
                    f"Shapefile does not exist. Real path was: {operation_config['shapefilePath']}"
                )
                log.error(f"local path was  {shapefile_path.as_posix()}")
                return -1

    raw_data_dir = os.path.join(cwd, raw_data_path)
    num_files = [f for f in os.listdir(raw_data_dir) if ".zip" in f]
    if num_files:
        log.info("found {} zip files to process".format(len(num_files)))
    else:
        log.warning("No file found to process in {}".format(raw_data_dir))
        return 0

    processed_dir = os.path.join(cwd, final_data_path)
    if not os.path.exists(processed_dir):
        log.warning("output data directory does not exist.  Creating directory ...")
        os.mkdir(processed_dir)

    archive_dir = os.path.join(cwd, archive_data_path)
    if do_archive_data and not os.path.exists(archive_dir):
        log.warning(
            "archive_data is set to 'True' but there is no data_archived directory found. Creating the directory ..."
        )
        os.mkdir(archive_dir)

    log.debug("Checking data directories completed successfully")

    return 1


def apply_generic_operator(source: ProductIO, generic_parameters: dict):
    """
    Applies an operator generic_paramters['operatorName'] using all other parameters on source

    Parameters
    ----------
    source
        a S1 GRD file loaded via snappy's ProductIO function to be operatored on
    generic_paramters
        a dictionary of parameters. Will feed all parameters except 'operatorName'
        to the operator 'operatorName'
    """

    java_parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in generic_parameters.items():
        if (value is not None) and (key != "operatorName"):
            java_parameters.put(key, value)

    output = GPF.createProduct(generic_parameters["operatorName"], java_parameters, source)
    return output


def check_poly_intersects_image(poly: Polygon, source: ProductIO, boundary: int = 2000) -> None:
    """Check if polygon intersects image, code original author Foad Farivar"""
    data_boundary_java = snappy.ProductUtils.createGeoBoundary(source, 2000)
    image_poly = Polygon([(i.lon, i.lat) for i in list(data_boundary_java)])
    if poly is not None:
        if not image_poly.intersects(poly):
            log.error("Polygon does not intersect image. Raising an exception")
            log.error(f"    polygon given is {poly.wkt}")
            log.error(f"    Image polygon is {image_poly.wkt}")
            raise ValueError("Shapefile polygon does not overlap with image")
    return


def prepare_polygon_subset(polygon_params, source):
    """prepares the polygon parameters dictionary for a polygon subset"""
    # We need to delete the 'polygon' parameter
    polygon = Polygon(polygon_params.pop("polygon"))
    wkt_s = polygon.wkt
    check_poly_intersects_image(polygon, source)
    polygon_params["geoRegion"] = WKTReader().read(wkt_s)
    return polygon_params


def load_shapefile(shapefile_path: Path):
    """Load shapefile, code original author Foad Farivar"""
    try:
        r = shapefile.Reader(shapefile_path)
    except Exception as e:
        log.error(f"cannot read shapefile: {shapefile_path}")
        raise e
    g = []
    for s in r.shapes():
        g.append(pygeoif.geometry.as_shape(s))
    m = pygeoif.MultiPoint(g)
    wkt = str(m.wkt).replace("MULTIPOINT", "POLYGON(") + ")"
    log.info(f"WKT IS {wkt}")
    poly = shapely.wkt.loads(wkt)
    return poly


def prepare_shapefile_subset(shapefile_params, source, shapefile_subdirectory):
    """prepares the shapefile parameters dictionary for a polygon subset"""
    # We need to delete the shapefilePath parameter
    shapefile_path = Path(shapefile_params.pop("shapefilePath"))
    # Shapefile_path is entered as a global path. Adjust to its local docker path
    shapefile_path = Path(shapefile_subdirectory) / shapefile_path.name
    polygon = load_shapefile(shapefile_path)
    wkt_s = polygon.wkt
    check_poly_intersects_image(polygon, source)
    shapefile_params["geoRegion"] = WKTReader().read(wkt_s)
    return shapefile_params


def check_file_processed(fname, final_data_path="./data/data_processed/", zip_file_given=True):
    """Checks if a file has already been processed"""
    fname = basename(fname)
    if zip_file_given:
        fname = re.sub("(.zip)$", "_processed.tif", fname)
    meta_dir = join(final_data_path, ".processed")
    file_suffix = ".done"
    meta_file_exists = isfile(join(meta_dir, fname + file_suffix))
    og_file_exists = isfile(join(final_data_path, fname))
    if meta_file_exists and og_file_exists:
        return True
    else:
        return False


def create_proc_metadata(fname, final_data_path="./data/data_processed/", zip_file_given=False):
    """Creates metadata that the file has been processed for future use in '.processed'."""
    import re

    fname = basename(fname)
    if zip_file_given:
        fname = re.sub("(.zip)$", "_processed.tif", fname)
    meta_dir = join(final_data_path, ".processed")
    Path(join(meta_dir, fname + ".done")).touch()
    return
