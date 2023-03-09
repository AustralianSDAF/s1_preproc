#!/bin/python

# User to configure the following parameters before running main.py

# =============================================================================
# File IO Configuration

# Specify your Working Directory (Please use absolute paths)
work_dir = "/data/InSAR_data"

# Specify your Raw Product Filepaths (Please use absolute paths)
# NOTE: REQUIRED TO READ THE FILES IN CHRONOLOGICAL ORDER (OLDEST FIRST)
filepath_1 = "/data/InSAR_data/Raw/S1B_IW_SLC__1SDV_20190702T032447_20190702T032514_016949_01FE47_69C5.zip"

filepath_2 = "/data/InSAR_data/Raw/S1A_IW_SLC__1SDV_20190708T032532_20190708T032559_028020_032A14_33CA.zip"

# Specify your output file format
# Allowed formats to write: GeoTIFF-BigTIFF,HDF5,Snaphu,BEAM-DIMAP,
# GeoTIFF+XML,PolSARPro,NetCDF-CF,NetCDF-BEAM,ENVI,JP2,
# Generic Binary BSQ,Gamma,CSV,NetCDF4-CF,GeoTIFF,NetCDF4-BEAM"
write_file_format = "GeoTIFF"

# Specify whether to delete intermediate products produced during processing
del_intermediate_products = True
# =============================================================================
# TOPSAR-Split Parameters
product_1_subswath = "IW2"
product_1_first = 3
product_1_last = 5

product_2_subswath = "IW2"
product_2_first = 1
product_2_last = 3

# =============================================================================
# SNAPHU Parameters
init_method = "MCF"
num_processors = 8

# =============================================================================
# Specify the type of INSAR Process to complete
# ELEVATION or DISPLACEMENT
processing = "ELEVATION"