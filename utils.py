#!/bin/env/python
#some functions are taken from https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy/blob/master/s1_preprocessing.py
#TODO: move parameters to config file

import imp
import logging

from pandas import isnull
import shapefile
import pygeoif
import os

from data.config import *

import snappy
from snappy import Product
from snappy import ProductIO
from snappy import ProductUtils
from snappy import WKTReader
from snappy import HashMap
from snappy import GPF

logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def pre_checks():
    """perform directory structure check

    :return: if return = 0 -> no file to processs | if return = -1 -> Error | else: Success
    :rtype: int
    """
    
    #chacking paths
    cwd = os.getcwd()
    log.debug("Checking data directories")

    if not os.path.exists(os.path.join(cwd, "data/config.py")):
        log.error("could not find config file in data/config.py")
        return -1

    if not os.path.exists(os.path.join(cwd, "data/data_raw/")):
        log.error("Raw data directory (data/data_raw) does not exist. Terminating execution ...")
        return -1
    
    raw_data_dir = os.path.join(cwd, "data/data_raw/")
    num_files = [f for f in os.listdir(raw_data_dir) if ".zip" in f]
    if num_files:
        log.info("found {} zip files to process".format(len(num_files)))
    else:
        log.warning("No file found in data_raw directory")
        return 0
    
    processed_dir = os.path.join(cwd, "data/data_processed/")
    if not os.path.exists(processed_dir):
        log.warning("data_processed directory does not exist.  Creating ...")
        os.mkdir(processed_dir)
    
    archive_dir = os.path.join(cwd, "data/data_archived/")
    from data.config import archive_data
    if archive_data and not os.path.exists(archive_data):
        log.warning("archive_data is set to 'True' but there is no data_archived directory found. Creating the directory ...")
        os.mkdir(archive_dir)
    log.debug("Checking data directories completed successfully")
    
    return 1
        

def apply_orbit_file(source):

    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

    for key,value in apply_orbit_file_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Apply-Orbit-File', parameters, source)
    return output


def calibration(source):

    parameters = HashMap()
    for key,value in calibration_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct("Calibration", parameters, source)
    return output 

def speckle_filtering(source):

    parameters = HashMap()
    for key,value in speckle_filtering_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Speckle-Filter', parameters, source)
    return output

def terrain_correction(source):
    
    parameters = HashMap()
    for key,value in terrain_correction_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Terrain-Correction', parameters, source)
    return output

def grd_boarder_noise(source):
    
    parameters = HashMap()
    for key,value in grd_boarder_noise_param.items():
        if value is not None:
            parameters.put(key, value)

    output = GPF.createProduct('Remove-GRD-Border-Noise', parameters, source)
    return output

def thermal_noise_removal(source):
    
    parameters = HashMap()
    for key,value in thermal_noise_removal_param.items():
        if value is not None:
            parameters.put(key, value)
    output = GPF.createProduct('ThermalNoiseRemoval', parameters, source)
    return output

def write_file(product, filename):

    ProductIO.writeProduct(product, filename, write_file_format)


def subset_from_polygon(source, wkt=None):

    if not wkt:
        polygon = polygon_param
    else:
        polygon = wkt
        
    #SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
    geometry = WKTReader().read(polygon)
    #HashMap = snappy.jpy.get_type('java.util.HashMap')
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters = HashMap()
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geometry)
    output = snappy.GPF.createProduct('Subset', parameters, source)

    return output

def subset_from_shapefile(source):

    path = shapefile_path
    #check path
    try:
        r = shapefile.Reader(path)

    except Exception:
        log.error("cannot read the shapefile in: {}".format(path))
        log.error(Exception)
    
    g=[]
    for s in r.shapes():
        g.append(pygeoif.geometry.as_shape(s)) 
    m = pygeoif.MultiPoint(g)
    wkt = str(m.wkt).replace("MULTIPOINT", "POLYGON(") + ")"
    output = subset_from_polygon(source, wkt)

    return output