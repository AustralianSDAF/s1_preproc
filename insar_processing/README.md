# Sentinel-1 InSAR Image Processing with SNAPPY
Author:
- Calvin Pang (calvin.pang@curtin.edu.au)

## Contents
- [Overview](#overview)
- [Setup (Conda)](#setup-conda)
- [References](#references)
___
## Overview
Processing pipeline for DEM Generation and Displacement Mapping from Sentinel-1 Interferometric Wide Swath products with ESA Sentinal Application Platform (SNAP 8.0) and Python 3.9.

![INSAR Processing Pipeline](INSAR_Processing_Flowchart.png)

For successful InSAR Processing, it is highly recommended to select an image pair with suitable properties.
- Short Temporal Baseline: Time between the first and second image should be kept as short as possible (Between 6 or 12 days)
- Suitable Perpendicular Baseline: Distance between the satellites’ positions at the time of image acquisition should be between 150 - 300m

Cannot be images acquired:
- Over vegetation or water areas
- Under changing moisture conditions (Advisable to select images acquired during dry periods and where no rainfall has occurred)
- Over moving objects

NOTE: 
- The orbit track spacing and revisit rate is significantly decreased at latitudes near the equator.
- Sentinel-1B has stopped data transmission from December 23, 2021 therefore you may be unable to obtain good interferometric products from this point forward as the phase difference cannot be exploited.
___
## Setup (Conda)
*Assuming you have already setup your Nimbus VM (Recommended Requirements: 16 Core CPU/ 64GB RAM)*
1. Create a conda environment   
  `conda create -n snap8 -c terradue snap=8.0.0 snapista gdal libgfortran5`
2. Activate the environment   
  `conda activate snap8`
3. Install Python packages    
  `pip install -r requirements.txt`
4. Configure SNAP Python API (SNAPPY) to use 80% available system memory 
    - Navigate to the directory containing your conda environment (e.g. `~/mambaforge/envs/snap8`)
    - Modify `.../snap/.snap/snap-python/snappy/snappy.ini` and set `java_max_mem` to 54G
    - Modify `.../snap/etc/snap.properties` and set `snap.jai.tileCacheSize` to 55296
5. Download SNAPHU
  `wget https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/snaphu-v2.0.5.tar.gz`
6. Unzip SNAPHU
  `tar -xvzf snaphu-v2.0.5.tar.gz`
7. Make SNAPHU
  `cd snaphu-v2.0.5/src ; make`
8. Add SNAPHU to System PATH by adding the following line to your `.bashrc` profile.  
  `export PATH=$PATH:/home/ubuntu/snaphu-v2.0.5/bin`

Note: Modify the paths as necessary depending on your machine.

## Usage
### Individual Processing
1. Navigate to the directory containing this repository  
  `cd s1a_proc/insar_processing`
2. Activate the conda environment  
  `conda activate snap8`
3. Configure `config.py` as required
4. Run downloader.py to download your Sentinel-1 IW SLC products  
  `python downloader.py`
5. Pre-screen your Sentinel-1 IW SLC products to check Perpendicular/Temporal Baselines and Subswath/Burst Selection for your AOI  
  `python precheck.py`
6. Check the output file and modify `config.py` to input your product pair.
7. Run the InSAR Processing  
  `python processing.py`

### Batch Processing
1. Navigate to the directory containing this repository  
  `cd s1a_proc/insar_processing`
2. Activate the conda environment  
  `conda activate snap8`
3. Configure `config.py` as required
4. Run main.py to download, pre-screen and process your products.  
  `python main.py`
  
___
## Output Product Information
DEM Products
- Band 1: displacement_VV
- Band 2: coherence_VV
- Band 3: phase_VV

Displacement Products
- Band 1: elevation_VV
- Band 2: coherence_VV
- Band 3: phase_VV

## References
1. [DEM Generation with Sentinel-1](http://step.esa.int/docs/tutorials/S1TBX%20DEM%20generation%20with%20Sentinel-1%20IW%20Tutorial.pdf)
2. [Displacement Mapping with Sentinel-1](http://step.esa.int/docs/tutorials/S1TBX%20TOPSAR%20Interferometry%20with%20Sentinel-1%20Tutorial_v2.pdf)
3. [Phase Unwrapping with SNAPHU](https://step.esa.int/main/snap-supported-plugins/snaphu/)
4. [SNAP GPT](http://step.esa.int/docs/tutorials/SNAP_CommandLine_Tutorial.pdf)
5. [S-1 TOPS SPLIT Analyzer (STSA)](https://github.com/pbrotoisworo/s1-tops-split-analyzer)
6. [Sentinel-1 Revisit and Coverage](https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-1-sar/revisit-and-coverage)
