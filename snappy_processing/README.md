# Snappy processing
### Sentinel-1 image pre-processing with snappy as a docker image
Author(s):
- Foad Farivar 
- Leigh Tyers

## Contents
- [Overview](#overview)
- [Setup (Docker)](#setup-steps-docker)
- [Setup (Conda)](#setup-steps-conda)
- [Custom processing options](#custom-processing-options)
- [Directory structure](#directory-structure)
- [References](#references)
___

## Overview 
Ubuntu 18.04 based docker image with ESA Sentinel Application Platform (SNAP 9.0) and Python 3.6, for processing Sentinel 1 imagery to analysis ready data.

The following functions are included in the pre-processing steps (in `utils.py`):
- Orbit file application.
- Image subsetting from either a polygon or shapefile.
- Thermal noise removal.
- GRD border noise removal.
- Image calibration.
- Speckle filtering.
- Terrain correction
- Writing to selected format file
- user-provided SNAP operations, see below

It also now allows command line input. Try the `--help` option when launching the docker image for allowable parameters.

**(The order of execution can be changed in `main_config.py` by changing `s1tbx_operator_order`)** 

---
## Running the image yourself
This image is designed primarily to be run from the `process_and_download.py` script in the directory above. If you wish to run just this image, these steps are for you.


### Setup steps (Docker)
(a) Clone this repository to your local directory: `git clone <this repo>` and then `cd <this repo>/snappy_processing`.

(b) Check the config file (`./data/config.py`) to set/change the pipeline parameters.

(c) Build the docker image with user_id arguments:
```
    docker build -t landgate
```

(d) Copy the row .zip files to raw_data_path (by default in `./data/data_raw`).

(e) Run the docker image: `docker run --rm -it -v <directory with "data_raw">:/app/data landgate`. If you are running on a root install of docker, you should also provide the `--user $(id -u):$(id -g)` parameter, or else files created may be owned by root.

(f) The final processed image will be saved in final_data_path (by default in `./data/data_processed`)

### Setup steps (Conda)
These steps may or may not work, and might be dependent on the version of ubunt you are running on.
(a) Clone this repository to your local directory: `git clone <this repo>` and then `cd <this repo>/snappy_processing`.

(b) Check the config file (`./data/config.py`) to set/change the pipeline parameters.

(c) Download SNAP: `wget  --progress=bar https://download.esa.int/step/snap/9.0/installers/esa-snap_sentinel_unix_9_0_0.sh`

(d) Create a conda environment:  `conda create --name landgate python=3.6`

(e) Activate the environment `conda activate landgate`.

(f) Install SNAP: `bash esa-snap_sentinel_unix_9_0_0.sh`

(g) Configure SNAP for Python:
```
> cd ~/snap/bin/
> ./snappy-conf {python_path}
> cd ~/.snap/snap-python/snappy 
> python3 setup.py install
> python3 -m sys.path.append('<snappy-dir>')
```
(h) Install packages: `pip install -r requirements.txt`.

(i) Run the main file: `python3 main.py`

(j) The final processed image will be saved in final_data_path (by default in `./data/data_processed`)


### Custom processing options
By creating a dictionary in `config.py` and inserting it as needed into the list , one is able to run almost any snap process.  
Simply create a dictionary with the key `operatorName` whose value is the operation, and give any other needed parameters. Then insert this into `s1tbx_operator_order`, at the location specified. e.g. the following will attempt to run another `Remove-GRD-Border-Noise` after the first (whether or not that will work).
```py
second_grd_border_noise_param = {
    "operatorName": "Remove-GRD-Border-Noise",
    "trimThreshold": 0.5,
    "borderLimit": 1000,
}
s1tbx_operator_order = [
    apply_orbit_file_param,
    thermal_noise_removal_param,
    grd_border_noise_param,
    second_grd_border_noise_param,
]
```


### Directory structure

```
.
├── Dockerfile
├── README.md
├── __init__.py
├── data
│   ├── config.py
│   ├── data_archived - Will be generated if needed
│   ├── data_processed - Will be generated
│   └── data_raw - Will be generated
├── main.py
├── requirements.txt
├── snap
│   ├── about.py
│   ├── config_python.sh
│   └── response.varfile
└── utils.py
```

## References

1. https://github.com/mundialis/esa-snap
2. https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
3. http://step.esa.int/docs/tutorials/tutorial_s1floodmapping.pdf

