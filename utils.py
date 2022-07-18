#!/bin/env/python

import logging
import shapefile
import pygeoif
import os

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

    cwd = os.getcwd()

    #chack paths
    log.debug("Checking data directories")
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
    if os.path.exists(processed_dir):
        
        




def apply_orbit_file(source):

    log.info("Applying orbit file ...")
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters.put('Apply-Orbit-File', True)
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('continueOnFail', False)
    
    output = GPF.createProduct('Apply-Orbit-File', parameters, source)
    log.info("Done!")
    return output

