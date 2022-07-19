#!/bin/env/python
### Please DO NOT change the relative directory of this config file ####

#=======================================================================
# pre-processing steps
#=======================================================================

do_apply_orbit_file = True
# parameters - Assigne None if you want to skip a parameter
apply_orbit_file_param = {
    'orbitType' : 'Sentinel Precise (Auto Download)',
    'polyDegree' : '3',
    'continueOnFail' : False,
    }
#=======================================================================

do_speckle_filtering = True
# parameters - Assigne None if you want to skip a parameter
speckle_filtering_param = {
    'sourceBands' : 'Sigma0_VV',
    'filter' : 'Lee',
    'filterSizeX' : '5',
    'filterSizeY' : '5',
    'dampingFactor' : '2',
    'estimateENL' : 'true',
    'enl' : '1.0',
    'numLooksStr' : '1',
    'windowSize' : None,
    'targetWindowSizeStr' : None,
    'sigmaStr' : '9.0',
    'anSize' : '50'
    }
#=======================================================================

do_calibration = True
# parameters - Assigne None if you want to skip a parameter
calibration_param = {
    'sourceBands' : 'Intensity_VV',
    'outputImageScaleInDb' :  False,
    'selectedPolarisations' : 'VV',
    'outputSigmaBand' : True,
    }
#=======================================================================

do_thermal_noise_removal = True
# parameters - Assigne None if you want to skip a parameter
thermal_noise_removal_param = {
    'removeThermalNoise' : True
}
#=======================================================================

do_terrain_correction = True
# parameters - Assigne None if you want to skip a parameter
terrain_correction_param = {
    'sourceBands' : 'Sigma0_VV',
    'demName' : 'SRTM 3Sec',
    'imgResamplingMethod' : 'BILINEAR_INTERPOLATION',
    'mapProjection' : 'WGS84',
    
}

do_grd_boarder_noise = False

do_subset_from_polygon = True
do_subset_from_shapefile = False

