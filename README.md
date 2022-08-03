# landgate-ASDAF project
###sentinel-1 image pre-processing pipeline
___

Ubuntu based docker image with  ESA Sentinel Application Platform (SNAP) and Python 3.6 installed, for pre-processing Sentinel 1 imagery to analysis ready data.

The following functions are included in the pre-processing steps:
1. Orbit file application.
2. Image subsetting from either a polygon or shapefile.
3. Thermal noise removal.
4. GRD border noise removal.
5. Image calibration.
6. Speckle filtering.
7. Terrain correction
8. Writing to selected format file

## Setup steps
(a) Clone this repository to your local directory: `git clone git@github.com:CurtinIC/landgate.git`.

(b) Check the config file (`./data/config.py`) to set/change the pipeline parameters.

(c) Build the docker image: `docker build -t landgate:{version} .`.

(d) Copy the row .zip files to raw_data_path (by default in `./data/data_raw`).

(e) Run the docker image: `docker run --rm -it -v ${PWD}/data/:/app/data landgate:{version}`.

(f) The final processed image will be saved in final_data_path (by default in `./data/data_processed`)


