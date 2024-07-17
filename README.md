# Sentinel-1 image pre-processing pipeline

Author(s):
- Leigh Tyers 
- Foad Farivar  

Proof of concept insar processing (see insar_processing directory):
- Calvin Pang

## Contents
- [Overview](#overview)
- [Installation & Pre-requisites](#installation-and-pre-requisites)
- [Downloading tool](#downloading-tool)
- [Processing tool](#processing-tool)
- [References](#references)
___

## Overview
A python repository for automatically acquiring and processing Sentinel 1 imagery over Australia.

This package is composed of a few parts
- A processing tool 
- A downloading tool, which calls the processing tool
- A POC insar processing tool
The downloader requires python >= 3.7 , while the processing tool requires python==3.6 (as of writing, python 3.6 has been depreciated). This discrepency is solved by building a docker image for the processing tool, which is called from the overarching python 3.10 script.

Due to there currently (as of writing) being only one Sentinel-1 satellite (S1B is down, S1C is yet to launch), we expect use of this tool to be only the processing tool and downloading tool.


## Installation and Pre-requisites

1. This software is only designed to work on Linux, tested on ubuntu 18.04-22.04.
If you are on windows, you may be able to get this to work using WSL

2. Clone or download the directory to your local computer, e.g. 
	```
	git clone <git repo url>
	```
	Extract the folder if needed, and navigate in a shell to the directory using `cd`

3. Install conda&mamba through [miniforge](https://github.com/conda-forge/miniforge)  
You may need to restart your shell, or run `source ~/.bashrc` after this.  
You should now see the enviornment name `(base)` prefixed in your shell.
`mamba` is a drop in, faster replacement for conda. Any `mamba` commands listed here can be swapped out for `conda` if that's your kettle o' fish.

5. Install the environment:
	```
	mamba env create --file env.yml
	```

6. Install [docker engine](https://docs.docker.com/engine/install/) - Docker Desktop is not needed. , or for WSL (untested), [this](https://docs.docker.com/desktop/wsl/) may be helpful

## Usage
1. Install pre-requisites, then activate the enviornment before processing:
	```
	mamba activate s1_preproc
	```  
	You should now see the environment name `(s1_preproc)` prefixed in your shell

2. Modify the config file `main_config.py` with your desired parameters. In particular, modify `bounds`, `start_date`, and `end_date`
e.g.
	```
	data_directory = '/data/S1_data'

	bounds = [116.29493,-20.55255, 117.77237,-21.55667]

	start_date = "2021-01-20"
	end_date = "2021-02-20"

	# The std_out will be logged here (relative to data_directory)
	log_fname = "debug.log"

	# Delete intermediate files in the processing (ie raw output of snappy)
	del_intermediate = True

	# Whether or not to download files from THREDDS
	download_from_thredds = True
	...
	```

3. From the local directory, run `python process_and_download.py`

4. The program will run, downloading any nescesary remote sensing data and acillary data (orbitfiles, DEMs). All these files should be stored in the location defined in the config file.


## Setting up a cronjob to automatically look for files.
Once the program is set up, you can set it to automatically run with `cron` by running `crontab -e`
and inserting the following lines:
```
SHELL=/bin/bash
BASH_ENV=~/.bashrc_conda
* */2 * * * run-one conda run --no-capture-output -n base python3 <DIR>/process_and_download.py
```
This will set the program once every 2 hours, using the conda/mamba environment `base`, but only if the same command isnt already running (ie if it's processing and taking some time, it wont relaunch itself).   

If you want to change the time between re-launch attempts, change `* */2 * * *` at the start of the third line to the equivalent cron schedule (you can see what you want command you may want for what cycle here https://crontab.guru/)

# Specifics
## Downloading tool
The downloading tool used is [eodag](https://eodag.readthedocs.io/en/stable/). EODAG allows easy authentication, searching, and downloading of a variety of data products from multiple providers. [SARA (Sentinel Australasia Regional Access)](https://copernicus.nci.org.au/sara.client/) now supported in the official conda-forge and py-pi releases (ver >=2.8.0).
```
python -m pip install eodag[all]
```
Unfortunately, as mentioned above, it seems to need a version of requests which needs python>=3.7 (python 3.6 is now depreciated).

For more information on how to use EODAG, see the [API user guide overview](https://eodag.readthedocs.io/en/stable/notebooks/api_user_guide/1_overview.html).

## Processing tool
### Snappy processing
The processing tool first uses snappy. As snappy requires python 3.6 (which is incompatible with the downloading tool), a docker image is built. See [snappy_processing/README.md](snappy_processing/README.md) for steps on how to set up the docker container. Docker should be included on the Nimbus ubuntnu 22.04 image.

The snappy processing will do the following:
- Apply the orbit file
- Speckle filtering
- Radiometric calibration
- Thermal Noise removal
- Terrain Correction
- GRD Border noise removal
- Subsetting (if requested, by default off)

Although any defined operation should work. Simply:
1. Create a new dictionary in the config file with the key `operatorName` whose corresponding value is the SNAP operator, and give it any needed parameters. e.g:
	```py
	second_grd_border_noise_param = {
		"operatorName": "Remove-GRD-Border-Noise",
		"trimThreshold": 0.5,
		"borderLimit": 1000,
	}
	```
2. Insert this new dictionary into the list `s1tbx_operator_order` at the place in the processing chain you wish your new operator to be processed at.  
e.g. the following will run the operation above after the first grd_border_noise removal, but before the terrain correction:
	```py
	s1tbx_operator_order = [
		apply_orbit_file_param,
		thermal_noise_removal_param,
		grd_border_noise_param,
		second_grd_border_noise_param,
    	terrain_correction_param,
	]
	```

### GDAL Processing
Snappy by default doesnt apply adequate compresion to the geotiff, so once the snappy processing is completed, the raster output is then transformed into a [COG (Cloud Optimized GeoTiff)](https://www.cogeo.org/) with extra lossless compression applied. With lossless compression applied (`COMPRESS=LZW, PREDICTOR=2`), the COG is half the size of the snappy output, but about 15-25% larger than the equivalent standard geotiff with the same compression flags applied.
The benefit of the COG format is that it is much faster to load for programs that properly understand it (QGIS, ArcGIS Pro, Rasterio, etc.), while still generally being backwards compatible with older software. My experience is that loading a standard 1-2GB Sentinel-1 raster into QGIS will take quite some time, whereas a COG will load almost immediatly, and will zoom, pan, and perform local histogram stretches MUCH faster.

## General Notes
The docker image is currently re-launched every time a file is needed to be processed. Experimenting with keeping it open to process everything did not yield a significant time saving, despite the small amount of overhead of launching snappy over and over again.
The largest reasons for this are:
- The overhead for launching snappy is relatively small compared with the processing time
- The processing time has a significant proportion spent processing supporting products from ESA (eg SRTM dems)
- These supporting DEMs products do not seem to be re-used by snap within the same session, and need to be re-processed each time.

For these reasons, the processing is currently done per file, by:
1. Downloading a file
2. Processing that file with snappy
3. Post-processing that file
4. Moving to the next file

This was done to preserve modularity, and to more easily understand the progress of the program when processing a large number of files.

## Wishlist
Future steps to make the program better
- [ ] Preserve DEM files between runs
- [ ] Full docker image with everything ready to go as a command line program
- [ ] Script to create & remove cronjob (currently just manually done)
- [ ] Sphinx documentation
- [x] Check if container exists, build it if not
- [ ] Include support for singularity/podman


## References

1. https://github.com/mundialis/esa-snap/tree/master
2. https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
3. http://step.esa.int/docs/tutorials/tutorial_s1floodmapping.pdf
4. https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy

