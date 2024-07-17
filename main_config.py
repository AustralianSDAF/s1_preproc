#!/bin/env/python
# =======================================================================
# Non-docker options you'd likely want to change.
# Try to only change this section unless you know what you're doing

# Directory to save files to
data_directory = "~/data/S1_data"

# minlon, minlat, maxlon, maxlat to search between. Other code should fix issues with giving minlat as maxlat etc.
bounds = [116.29493, -20.55255, 117.77237, -21.55667]

# Period to search between
start_date = "2023-01-31"
end_date = "2023-02-07"

# You shouldnt need to change the search options below.
geo = {"lonmin": bounds[0], "latmin": bounds[1], "lonmax": bounds[2], "latmax": bounds[3]}

# Full search criteria, must be a dictionary
search_criteria = {
    "productType": "S1_SAR_GRD",
    "start": start_date,
    "end": end_date,
    "sensorMode": "IW",
    "geom": geo,
}


# The std_out will be logged here. (relative to data_directory)
log_fname = "debug.log"

# Delete intermediate files in the processing (ie raw output of snappy)
del_intermediate = True

# Whether or not to download files from THREDDS
download_from_thredds = True


### Below are the pre-processing config options          ####
### Feel free to change them as you want to,             ####
### but the defaults should work well enough             ####

# =======================================================================
# pre-processing steps Parameters
# Assigne None if you do not want to set a parameter/want to leave it as a default
# =======================================================================

# To properly orthorectify the image, the orbit file is applied using the Apply-Orbit-File GPF module.
apply_orbit_file_param = {
    "operatorName": "Apply-Orbit-File",
    "orbitType": "Sentinel Precise (Auto Download)",
    "polyDegree": "3",
    "continueOnFail": False,
}
# =======================================================================

# Remove speckle noise from the imagary
speckle_filtering_param = {
    "operatorName": "Speckle-Filter",
    "sourceBands": "Sigma0_VV",
    "filter": "Lee",
    "filterSizeX": "5",
    "filterSizeY": "5",
    "dampingFactor": "2",
    "estimateENL": True,
    "enl": "1.0",
    "numLooksStr": "1",
    "windowSize": None,
    "targetWindowSizeStr": "3x3",
    "sigmaStr": "0.9",
    "anSize": "50",
}
# =======================================================================

# Convert digitnal numbers (DN's) into backscatter coefficient (sigma-naught) values
radiometric_calibration_param = {
    "operatorName": "Calibration",
    "sourceBands": "Intensity_VV",
    "outputImageScaleInDb": False,
    "selectedPolarisations": "VV",
    "outputSigmaBand": True,
}
# =======================================================================

# apply thermal noise removal to input data
thermal_noise_removal_param = {"operatorName": "ThermalNoiseRemoval", "removeThermalNoise": True}
# =======================================================================

# Apply terrain correction to the product
terrain_correction_param = {
    "operatorName": "Terrain-Correction",
    "sourceBands": "Sigma0_VV",
    "demName": "SRTM 3Sec",
    "imgResamplingMethod": None,
    "mapProjection": None,
    "pixelSpacingInMeter": 10.0,
    "saveProjectedLocalIncidenceAngle": None,
}

# =======================================================================

# Removes border noise in a GRD image
grd_border_noise_param = {
    "operatorName": "Remove-GRD-Border-Noise",
    "trimThreshold": 0.5,
    "borderLimit": 1000,
}
# =======================================================================
# Polygon to subset (if desired) as a list of [long, lat] coordinates
subset_polygon_bounds = [
    [125.54647, -17.94607],
    [125.54647 - 18.97182],
    [126.12290 - 18.97182],
    [126.12290 - 17.94607],
    [125.54647 - 17.94607],
]

# "polygon" is not passed to the
polygon_params = {
    "operatorName": "Subset",
    "polygon": subset_polygon_bounds,
    "copyMetadata": True,
}

# This path is your system global path, not a local docker path
shapefile_subset_params = {
    "operatorName": "Subset",
    "shapefilePath": "~/data/S1_data/",
    "copyMetadata": True,
}
# =======================================================================
# Operator Order
# Put any parameters above into the "s1tbx_operator_order"
# list below and they will be processed in that order.
# Remove or comment out an operators parameters
# and it will not be applied

# Any generic operator single-source oeprator can
# be applied by making a dictionary with the operators'
# name and any other parameters, then including it in
# s1tbx_operator_order below.
#
# NB: Currently shapefile subsetting do not work.

s1tbx_operator_order = [
    apply_orbit_file_param,
    thermal_noise_removal_param,
    grd_border_noise_param,
    radiometric_calibration_param,
    speckle_filtering_param,
    terrain_correction_param,
]


# =======================================================================


write_file_format = "GeoTIFF"
# Allowed formats to write: GeoTIFF-BigTIFF,HDF5,Snaphu,BEAM-DIMAP,
# GeoTIFF+XML,PolSARPro,NetCDF-CF,NetCDF-BEAM,ENVI,JP2,
# Generic Binary BSQ,Gamma,CSV,NetCDF4-CF,GeoTIFF,NetCDF4-BEAM"

# archive raw_data after processing is done?
do_archive_data = False


### Below are relative directories for the docker container.           ####
### Please DO NOT change these paths without knowing what you're doing ####
### These paths are relative for the docker container to use, and      ####
### may not reflect real paths.                                        ####
# =======================================================================
# Docker internal S1 downloaded files directory (relative to entrypoint paths)
raw_data_path = "./data/data_raw/"

# Docker  internal Path to save final processed data (relative to entrypoint paths)
final_data_path = "./data/data_processed/"

# Docker  internal Path to archive the processed raw data (relative to entrypoint paths)
archive_data_path = "./data/data_archived/"

# Docker  internal Path to auxillary data like orbitfiles (relative to entrypoint paths)
aux_location = "./data/aux_data"

# Docker  internal Path to shapefiles data like orbitfiles (relative to entrypoint paths)
shapefile_subdirectory = "./data/Polygons"

# Docker image name to use
docker_image_name = "s1_preproc"

# =======================================================================
# -------------------End of config file---------------------------------
# =======================================================================
