#!/bin/env/python
### Please DO NOT change the relative directory of this config file ####

# pre-processing steps

do_apply_orbit_file = True
# parameters
apply_orbit_file_param = {
    'orbitType' : 'Sentinel Precise (Auto Download)',
    'polyDegree' : '3',
    'continueOnFail' : 'false'
}

do_speckle_filtering = True
# parameters
speckle_filtering_param = {
    
}
do_calibration = True
do_thermal_noise_removal = True
do_terrain_correction = True
do_grd_boarder_noise = False

do_subset_from_polygon = True
do_subset_from_shapefile = False

