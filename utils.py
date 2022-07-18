#!/bin/env/python
#some functions are taken from https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy/blob/master/s1_preprocessing.py

import imp
import logging
import shapefile
import pygeoif
import os

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

    log.info("Applying orbit file ...")
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters.put('Apply-Orbit-File', True)
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('continueOnFail', False)
    
    output = GPF.createProduct('Apply-Orbit-File', parameters, source)
    log.info("Done!")
    return output


def subset_file(source, polygon):

    SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
    bounding_wkt = polygon
    geometry = WKTReader().read(bounding_wkt)
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    parameters = HashMap()
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geometry)
    product_subset = snappy.GPF.createProduct('Subset', parameters, source)

    return product_subset


def image_calibration(source, polarization, pols):
    log.info("Applying calibration ...")
    parameters = HashMap()
    parameters.put('outputSigmaBand', True)
    if polarization == 'DH':
        parameters.put('sourceBands', 'Intensity_HH,Intensity_HV')
    elif polarization == 'DV':
        parameters.put('sourceBands', 'Intensity_VH,Intensity_VV')
    elif polarization == 'SH' or polarization == 'HH':
        parameters.put('sourceBands', 'Intensity_HH')
    elif polarization == 'SV':
        parameters.put('sourceBands', 'Intensity_VV')
    else:
        log.warning("Applying to different polarization")
    parameters.put('selectedPolarisations', pols)
    parameters.put('outputImageScaleInDb', False)
    output = GPF.createProduct("Calibration", parameters, source)
    return output 

def speckle_filtering(source, filterSizeY , filterSizeX ):
    print('\tSpeckle filtering...')
    parameters = HashMap()
    parameters.put('filter', 'Lee')
    parameters.put('filterSizeX', filterSizeX)
    parameters.put('filterSizeY', filterSizeY)
    parameters.put('dampingFactor', '2')
    parameters.put('estimateENL', 'true')
    parameters.put('enl', '1.0')
    parameters.put('numLooksStr', '1')
    parameters.put('sigmaStr', '0.9')
    #parameters.put('anSize', '50')
    output = GPF.createProduct('Speckle-Filter', parameters, source)
    return output


def terrain_correction(source, proj, downsample):
    print('\tTerrain correction...')
    parameters = HashMap()
    parameters.put('demName', 'SRTM 3Sec')
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    #parameters.put('mapProjection', proj)       # comment this line if no need to convert to UTM/WGS84, default is WGS84
    parameters.put('saveProjectedLocalIncidenceAngle', True)
    parameters.put('saveSelectedSourceBand', True)
    while downsample == 1:                      # downsample: 1 -- need downsample to 40m, 0 -- no need to downsample
        parameters.put('pixelSpacingInMeter', 40.0)
        break
    output = GPF.createProduct('Terrain-Correction', parameters, source)
    return output

def grd_boarder_noise(source): #TODO
    print('\tRemove-GRD-Border-Noise...')
    parameters = HashMap()
    parameters.put('trimThreshold ', 0.5)
    parameters.put('borderLimit', 1000)

    output = GPF.createProduct('Remove-GRD-Border-Noise', parameters, source)
    return output

def write_file(product, filename, format="GeoTIFF"):
    ProductIO.writeProduct(product, filename, format)
    # Allowed formats to write: GeoTIFF-BigTIFF,HDF5,Snaphu,BEAM-DIMAP,
	# GeoTIFF+XML,PolSARPro,NetCDF-CF,NetCDF-BEAM,ENVI,JP2,
    # Generic Binary BSQ,Gamma,CSV,NetCDF4-CF,GeoTIFF,NetCDF4-BEAM