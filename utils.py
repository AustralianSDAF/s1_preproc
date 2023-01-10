#!/bin/env/python
# some functions are taken from https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy/blob/master/s1_preprocessing.py

# import imp
import logging
import shapefile
import pygeoif
import os
import snappy
# from snappy import Product
from snappy import ProductIO
# from snappy import ProductUtils
from snappy import WKTReader
from snappy import HashMap
from snappy import GPF
from shapely import wkt


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def pre_checks(
        filename, raw_data_path, shapefile_path, do_subset_from_shapefile, final_data_path,
        archive_data_path, do_archive_data
        ):
    """perform directory structure check

    :return: if return = 0 -> no file to processs | if return = -1 -> Error | else: Success
    :rtype: int
    """

    # checking paths
    cwd = os.getcwd()
    log.debug("Checking data directories")

    if not os.path.exists(os.path.join(cwd, "data/config.py")):
        log.error("could not find config file in data/config.py")
        return -1

    if (not os.path.exists(os.path.join(cwd, raw_data_path))) and (filename is not None):
        log.error("Raw data directory {} does not exist. Terminating execution ...".format(raw_data_path))
        return -1

    shapefile_abs_path = os.path.join(cwd, shapefile_path)
    if do_subset_from_shapefile and not os.path.isfile(shapefile_abs_path):
        log.error("shapefile does not exist in {}".format(shapefile_path))
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
        log.warning("archive_data is set to 'True' but there is no data_archived directory found. Creating the directory ...")
        os.mkdir(archive_dir)

    log.debug("Checking data directories completed successfully")

    return 1


def apply_orbit_file(source, apply_orbit_file_param):
    """To properly orthorectify the image, the orbit file is applied using the Apply-Orbit-File GPF module.

    :param source: input
    :type source: SNAP product object
    """

    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in apply_orbit_file_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Apply-Orbit-File', parameters, source)
    return output


def calibration(source, calibration_param):
    """calibrate the data to sigma-naught values

    :param source: input
    :type source: SNAP product object
    :return: calibrated product
    :rtype: SNAP product object
    """
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in calibration_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct("Calibration", parameters, source)
    return output


def speckle_filtering(source, speckle_filtering_param):
    """remove speckle noise from the imagary

    :param source: input
    :type source: SNAP product object
    :return: despeckled data
    :rtype: SNAP product object
    """

    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in speckle_filtering_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Speckle-Filter', parameters, source)
    return output


def terrain_correction(source, terrain_correction_param):
    """ apply terrain correction to the product

    :param source: input
    :type source: SNAP product object
    :return: terrain corrected object
    :rtype: SNAP product object
    """
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in terrain_correction_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Terrain-Correction', parameters, source)
    return output


def grd_border_noise(source, grd_border_noise_param):
    """_summary_

    :param source: _description_
    :type source: _type_
    :return: _description_
    :rtype: _type_
    """
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in grd_border_noise_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Remove-GRD-Border-Noise', parameters, source)
    return output


def thermal_noise_removal(source, thermal_noise_removal_param):
    """apply thermal noise removal to input data

    :param source: input
    :type source: SNAP product object
    :return: thermal noise removed object
    :rtype: SNAP product object
    """
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key, value in thermal_noise_removal_param.items():
        if value is not None:
            parameters.put(key, value)
    output = GPF.createProduct('ThermalNoiseRemoval', parameters, source)
    return output


def subset_from_polygon(source, poly_inp=None):
    from shapely.geometry import Polygon
    import shapely
    if type(poly_inp) is str:     # should be a wkt string
        poly = wkt.loads(wkt_s)
        wkt_s = poly_inp
    elif isinstance(poly_inp, Polygon):
        poly = poly_inp
        wkt_s = poly.wkt
    elif poly_inp is not None:    # Try loading it directly with shapely
        poly = Polygon(poly_inp)
        wkt_s = poly.wkt
    else:
        wkt_s = None
        poly = None

    # check if polygon inside the image
    data_boundary_java = snappy.ProductUtils.createGeoBoundary(source, 2000)
    image_poly = Polygon([(i.lon, i.lat) for i in list(data_boundary_java)])
    if(poly is not None):
        if(not image_poly.intersects(poly)):
            return source

    # SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
    geometry = WKTReader().read(wkt_s)

    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geometry)
    output = GPF.createProduct('Subset', parameters, source)

    return output


def subset_from_shapefile(source, shapefile_path=None):
    import shapely
    from shapely.geometry import Polygon

    if(shapefile_path is not None):
        path = os.path.abspath(shapefile_path)
    else:
        path = shapefile_path
    # check path
    try:
        r = shapefile.Reader(path)
    except Exception as e:
        log.info(f"Files in dir are {os.listdir(os.path.dirname(path))}")
        log.error("cannot read the shapefile in: {}".format(path))
        raise e

    g = []
    for s in r.shapes():
        g.append(pygeoif.geometry.as_shape(s))
    m = pygeoif.MultiPoint(g)
    wkt = str(m.wkt).replace("MULTIPOINT", "POLYGON(") + ")"
    log.info(f"WKT IS {wkt}")
    poly = shapely.wkt.loads(wkt)

    data_boundary_java = snappy.ProductUtils.createGeoBoundary(source, 2000)
    image_poly = Polygon([(i.lon, i.lat) for i in list(data_boundary_java)])
    if(poly is not None):
        if(not image_poly.intersects(poly)):
            return source

    output = subset_from_polygon(source, wkt)

    return output
