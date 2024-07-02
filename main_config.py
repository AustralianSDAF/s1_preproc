#!/bin/env/python

# =======================================================================
# Non-docker stuff options you'd likely want to actually change.
# Try to keep changes to this section alone unless you know what you're doing

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

# The std_out will be logged here
log_fname = "~/data/S1_data/debug.log"

# Delete intermediate files in the processing (ie raw output of snappy)
del_intermediate = True

# Whether or not to download files from THREDDS
download_from_thredds = True

### Below are relative directories for the docker container.           ####
### Please DO NOT change these paths without knowing what you're doing ####
### These paths are relative for the docker container to use, and      ####
### may not reflect real paths.                                        ####
# =======================================================================
# S1 downloaded files directory (relative to entrypoint paths)
raw_data_path = "./data/data_raw/"

# Path to save final processed data (relative to entrypoint paths)
final_data_path = "./data/data_processed/"

# Path to archive the processed raw data (relative to entrypoint paths)
archive_data_path = "./data/data_archived/"

# Path to auxillary data like orbitfiles
aux_location = "./data/aux_data"


### Below are the pre-processing config options          ####
### Feel free to change them as you want to,             ####
### but the defaults should work well enough             ####
###                                                      ####
### It also contains some parameters similar             ####
### to the above, which are local paths in the docker    ####
### container and should **NOT** be changed              ####
# =======================================================================
# pre-processing steps
# =======================================================================

do_apply_orbit_file = True
# parameters - Assigne None if you do not want to set a parameter
apply_orbit_file_param = {
    "orbitType": "Sentinel Precise (Auto Download)",
    "polyDegree": "3",
    "continueOnFail": False,
}
# =======================================================================

do_speckle_filtering = True
# parameters - Assigne None if you do not want to set a parameter
speckle_filtering_param = {
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

do_calibration = True
# parameters - Assigne None if you do not want to set a parameter
calibration_param = {
    "sourceBands": "Intensity_VV",
    "outputImageScaleInDb": False,
    "selectedPolarisations": "VV",
    "outputSigmaBand": True,
}
# =======================================================================

do_thermal_noise_removal = True
# parameters - Assigne None if you do not want to set a parameter
thermal_noise_removal_param = {"removeThermalNoise": True}
# =======================================================================

do_terrain_correction = True
# parameters - Assigne None if you do not want to set a parameter
terrain_correction_param = {
    "sourceBands": "Sigma0_VV",
    "demName": "SRTM 3Sec",
    "imgResamplingMethod": None,
    "mapProjection": None,
    "pixelSpacingInMeter": 10.0,
    "saveProjectedLocalIncidenceAngle": None,
}
# =======================================================================

do_grd_border_noise = True
# parameters - Assigne None if you do not want to set a parameter
grd_border_noise_param = {"trimThreshold": 0.5, "borderLimit": 1000}
# =======================================================================
# If using the scrip process_and_download.py, you should keep these as False,
# unless you want a hard override (but I cant guarentee that it would work)
do_subset_from_polygon = False
polygon_param = "POLYGON ((125.54647 -17.94607, \
                            125.54647 -18.97182, \
                            126.12290 -18.97182, \
                            126.12290 -17.94607, \
                            125.54647 -17.94607))"


do_subset_from_shapefile = False
# local Path to shapefile if subset_from_shapefile is enabled
shapefile_path = "./data/data_raw/example.shp"
# =======================================================================

write_file_format = "GeoTIFF"
# Allowed formats to write: GeoTIFF-BigTIFF,HDF5,Snaphu,BEAM-DIMAP,
# GeoTIFF+XML,PolSARPro,NetCDF-CF,NetCDF-BEAM,ENVI,JP2,
# Generic Binary BSQ,Gamma,CSV,NetCDF4-CF,GeoTIFF,NetCDF4-BEAM"

# archive raw_data after processing is done?
do_archive_data = False
#
# =======================================================================
# -------------------End of config file---------------------------------
# =======================================================================
