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
    'pixelSpacingInMeter' : None,
    'saveProjectedLocalIncidenceAngle' : True
    }
#=======================================================================

do_grd_boarder_noise = False
# parameters - Assigne None if you want to skip a parameter
grd_boarder_noise_param = {
    'trimThreshold' : 0.5,
    'borderLimit' : 1000
    }
#=======================================================================

do_subset_from_polygon = True
subset_from_polygon_param = {
    "wkt" : 'POLYGON ((-157.79579162597656 71.36872100830078, -155.4447021484375 71.36872100830078, \
                    -155.4447021484375 70.60020446777344, -157.79579162597656 70.60020446777344, \
                    -157.79579162597656 71.36872100830078))'
}

do_subset_from_shapefile = False
subset_from_shapefile_param = {
    "path_to_.shp" : ""
}
