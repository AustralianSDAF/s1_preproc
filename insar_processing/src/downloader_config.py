#!/bin/env/python

# =======================================================================
# Non-docker stuff options you'd likely want to actually change.
# Try to keep changes to this section alone unless you know what you're doing

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
