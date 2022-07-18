#!/bin/env/python

import logging
import shapefile
import pygeoif

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

