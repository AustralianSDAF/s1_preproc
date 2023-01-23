# Landgate-ASDAF project
### Sentinel-1 image pre-processing pipeline
Author(s):
- Foad Farivar (foad.farivar@curtin.edu.au)
- Leigh Tyers (leigh.tyers@curtin.edu.au)

## Contents
- [Overview](#overview)
- [Setup (Docker)](#setup-steps-docker)
- [Setup (Conda)](#setup-steps-conda)
- [Directory structure](#directory-structure)
- [References](#references)
___

## Overview 
Ubuntu 18.04 based docker image with the latest  ESA Sentinel Application Platform (SNAP 9.0) and Python 3.6, for processing Sentinel 1 imagery to analysis ready data.

The following functions are included in the pre-processing steps (in `utils.py`):
- Orbit file application.
- Image subsetting from either a polygon or shapefile.
- Thermal noise removal.
- GRD border noise removal.
- Image calibration.
- Speckle filtering.
- Terrain correction
- Writing to selected format file

It also now allows command line input. Try the `--help` option when launching the docker image for allowable parameters.

**(The order of execution can be changed in `main.py`)** 

## Setup steps (Docker)
(a) Clone this repository to your local directory: `git clone git@github.com:CurtinIC/landgate.git` and then `cd landgate/snappy_processing`.

(b) Check the config file (`./data/config.py`) to set/change the pipeline parameters.

(c) Build the docker image with user_id arguments:
```
    docker build -t landgate \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) .
```

(d) Copy the row .zip files to raw_data_path (by default in `./data/data_raw`).

(e) Run the docker image: `docker run --rm -it -v <directory with "data_raw">:/app/data landgate`.

(f) The final processed image will be saved in final_data_path (by default in `./data/data_processed`)

## Setup steps (Conda)
(a) Clone this repository to your local directory: `git clone git@github.com:CurtinIC/landgate.git` and then `cd landgate/snappy_processing`.

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

## Directory structure

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

1. https://github.com/mundialis/esa-snap/tree/master
2. https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
3. http://step.esa.int/docs/tutorials/tutorial_s1floodmapping.pdf
4. https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy

