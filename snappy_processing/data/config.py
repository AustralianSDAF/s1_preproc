#!/bin/env/python
### Please DO NOT change the relative directory of this config file ####

### NB: THIS CONFIG FILE IS HERE FOR TESTING PURPOSES.
### CHANGING THIS WILL NOT CHANGE THE
### FUNCTIONALITY OF THE DOCKER IMAGE.
###
### INSTEAD< CHANGE "../main_config.py". THAT CONFIG FILE
### WILL BE MOVED TO THE APPROPRIATE DIRECTORY WHEN RUN IN DOCKER

#=======================================================================
# S1 downloaded files directory (relative to CWD paths)
raw_data_path = "./data/data_raw/"

# Path to save final processed data (relative to CWD paths)
final_data_path = "./data/data_processed/"

# Path to archive the processed raw data (relative to CWD paths)
archive_data_path = "./data/data_archived/"

#=======================================================================
# pre-processing steps
#=======================================================================

do_apply_orbit_file = True
# parameters - Assigne None if you do not want to set a parameter
apply_orbit_file_param = {
    'orbitType' : 'Sentinel Precise (Auto Download)',
    'polyDegree' : '3',
    'continueOnFail' : False,
    }
#=======================================================================

do_speckle_filtering = True
# parameters - Assigne None if you do not want to set a parameter
speckle_filtering_param = {
    'sourceBands' : 'Sigma0_VV',
    'filter' : 'Lee',
    'filterSizeX' : '5',
    'filterSizeY' : '5',
    'dampingFactor' : '2',
    'estimateENL' : True,
    'enl' : '1.0',
    'numLooksStr' : '1',
    'windowSize' : None,
    'targetWindowSizeStr' : '3x3',
    'sigmaStr' : '0.9',
    'anSize' : '50'
    }
#=======================================================================

do_calibration = True
# parameters - Assigne None if you do not want to set a parameter
calibration_param = {
    'sourceBands' : 'Intensity_VV',
    'outputImageScaleInDb' :  False,
    'selectedPolarisations' : 'VV',
    'outputSigmaBand' : True,
    }
#=======================================================================

do_thermal_noise_removal = True
# parameters - Assigne None if you do not want to set a parameter
thermal_noise_removal_param = {
    'removeThermalNoise' : True
    }
#=======================================================================

do_terrain_correction = True
# parameters - Assigne None if you do not want to set a parameter
terrain_correction_param = {
    'sourceBands' : 'Sigma0_VV',
    'demName' : 'SRTM 3Sec',
    'imgResamplingMethod' : None,
    'mapProjection' : None,
    'pixelSpacingInMeter' : 10.0,
    'saveProjectedLocalIncidenceAngle' : None
    }
#=======================================================================

do_grd_border_noise = True
# parameters - Assigne None if you do not want to set a parameter
grd_border_noise_param = {
    'trimThreshold' : 0.5,
    'borderLimit' : 1000
    }
#=======================================================================

do_subset_from_polygon = False
polygon_param = 'POLYGON ((125.54647 -17.94607, \
                            125.54647 -18.97182, \
                            126.12290 -18.97182, \
                            126.12290 -17.94607, \
                            125.54647 -17.94607))'


do_subset_from_shapefile = False
shapefile_path = "./data/data_raw/island_boundary2.shp"
#=======================================================================

write_file_format = "GeoTIFF"
# Allowed formats to write: GeoTIFF-BigTIFF,HDF5,Snaphu,BEAM-DIMAP,
# GeoTIFF+XML,PolSARPro,NetCDF-CF,NetCDF-BEAM,ENVI,JP2,
# Generic Binary BSQ,Gamma,CSV,NetCDF4-CF,GeoTIFF,NetCDF4-BEAM"

#archive raw_data after processing is done?
do_archive_data = False
#
#=======================================================================
# -------------------End of config file---------------------------------
#=======================================================================
