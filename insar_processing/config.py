#!/bin/python

# User to configure the following parameters before running main.py

# =============================================================================
# File IO Configuration

# Specify your Working Directory (Please use absolute paths)
work_dir = "/data/S1_InSAR_Juukan"

# =============================================================================
# Downloader Configuation

# Area of Interest
# minlon, minlat, maxlon, maxlat to search between.
bounds = [117.02734629478383, -22.493086973432593, 117.31898748693916, -22.649316075632846]

# Period to search between
start_date = "2020-05-15"
end_date = "2020-06-15"

# You shouldnt need to change the search options below.
geo = {
    "lonmin": bounds[0],
    "latmin": bounds[1],
    "lonmax": bounds[2],
    "latmax": bounds[3],
}

# Full search criteria, must be a dictionary
search_criteria = {
    "productType": "S1_SAR_SLC",
    "start": start_date,
    "end": end_date,
    "sensorMode": "IW",
    "geom": geo,
    "orbitDirection" : 'Descending'
}

# The std_out will be logged here
log_fname = f"{work_dir}/debug.log"

# =============================================================================
# InSAR Processing Configuration

# Specify whether you wish to perform batch processing from the precheck output file
from_precheck = True

# Specify your Raw Product Filenames (They should be located in work_dir/data_raw)
# NOTE: REQUIRED TO READ THE FILES IN CHRONOLOGICAL ORDER (OLDEST FIRST)
filename_1 = "S1B_IW_SLC__1SDV_20200516T213951_20200516T214019_021612_029081_ACBD.zip"

filename_2 = "S1B_IW_SLC__1SDV_20200528T213952_20200528T214019_021787_0295B1_17C1.zip"

# Specify the type of InSAR Processing to complete
# ELEVATION or DISPLACEMENT
processing = "DISPLACEMENT"

# SNAPHU Parameters
init_method = "MCF"
num_processors = 8

# Specify your output file format
# Allowed formats to write: GeoTIFF-BigTIFF,HDF5,Snaphu,BEAM-DIMAP,
# GeoTIFF+XML,PolSARPro,NetCDF-CF,NetCDF-BEAM,ENVI,JP2,
# Generic Binary BSQ,Gamma,CSV,NetCDF4-CF,GeoTIFF,NetCDF4-BEAM"
write_file_format = "GeoTIFF"

# Specify whether to delete intermediate products produced during processing
del_intermediate_products = True

# =============================================================================
