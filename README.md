# Landgate-ASDAF project
### Sentinel-1 image pre-processing pipeline
Author(s):
- Leigh Tyers (leigh.tyers@curtin.edu.au)
- Foad Farivar (foad.farivar@curtin.edu.au)

## Contents
- [Overview](#overview)
- [Setup](#setup)
- [Downloading tool](#downloading-tool)
- [Processing tool](#processing-tool)
- [References](#references)
- [Manually setting up a NimbusVM](#manually-setting-up-a-nimbusvm)
___

## Overview
A python repository for automatically acquiring and processing Sentinel 1 imagery over Australia.

This package is composed of two parts, a processing tool and a downloading tool. The downloading tool requires python >= 3.7 , while the processing tool requires python==3.6 (as of writing, python 3.6 has been depreciated). This discrepency is solved by building a docker image for the processing tool, which is called from the overarching python 3.10 script.



## Setup
There is currently one way to set up the program:
1. Manually settting up the Nimbus VM. See [Manually setting up a NimbusVM](#manually-setting-up-a-nimbusvm)

Once the program is set up, you can set it to automatically run with `cron` by running `crontab -e`
and inserting the following lines:
```
SHELL=/bin/bash
BASH_ENV=~/.bashrc_conda
*/30 * * * * run-one conda run --no-capture-output -n base python3 /home/ubuntu/code/landgate/process_and_download.py
```
This will set the program once every 2 hours, using the conda/mamba environment `base`, but only if the same command isnt already running (ie if it's processing and taking some time, it wont relaunch itself).   

If you want to change the time between re-launch attempts, change `* */2 * * *` at the start of the third line to the equivalent cron schedule (you can see what you want command you may want for what cycle here https://crontab.guru/)

## Usage
First, edit main_config.py for your preferred configueration options.
Of particular importance are the following options:
```
data_directory = '/data/S1_data'

bounds = [116.29493,-20.55255, 117.77237,-21.55667]

start_date = "2021-01-20"
end_date = "2021-02-20"
...

# The std_out will be logged here
log_fname = "/data/S1_data/debug.log"

# Delete intermediate files in the processing (ie raw output of snappy)
del_intermediate = True

# Whether or not to download files from THREDDS
download_from_thredds = True

```
Set these as you wish.
- `data_directory` is the directory all the files will be downlaoded to and processed in.
- `start_date` and `end_date` are the start and end dates to search from. These are in the format YEAR-MONTH-DAY If you want to use find all products from a given date to the present, set end_date to `2100-01-01`. Unfortunately a type issue currently prevents using a larger number such as `3000-01-01

Once in the appropriate conda environment (if you used base, then the base environment is fine), run:
```
python3 process_and_download.py
```
- log_fname must exist, so if you need to just `mkdir data/S1_data && touch /data/S1_data/debug.log`
- if you set `download_from_thredds = False` you will be prompted for login information to authenticate with your registered SARA username/email and password

# Specifics
## Downloading tool
The downloading tool used is [eodag](https://eodag.readthedocs.io/en/stable/). EODAG allows easy authentication, searching, and downloading of a variety of data products from multiple providers. [SARA (Sentinel Australasia Regional Access)](https://copernicus.nci.org.au/sara.client/) now supported in the official conda-forge and py-pi releases (ver >=2.8.0).
```
python -m pip install eodag
```
Unfortunately, as mentioned above, it seems to need a version of requests which needs python>=3.7 (python 3.6 is now depreciated).

For more information on how to use EODAG, see the [API user guide overview](https://eodag.readthedocs.io/en/stable/notebooks/api_user_guide/1_overview.html).

## Processing tool
### Snappy processing
The processing tool first uses snappy. As snappy requires python 3.6 (which is incompatible with the downloading tool), a docker image is built. See [snappy_processing/README.md](snappy_processing/README.md) for steps on how to set up the docker container. Docker should be included on the Nimbus ubuntnu 22.04 image.

Currently the snappy processing will do the following:
- Apply the orbit file
- Speckle filtering
- Radiometric calibration
- Thermal Noise removal
- Terrain Correction
- GRD Border noise removal
- Subsetting (if requested, by default off)

### GDAL Processing
Snappy by default doesnt apply adequate compresion to the geotiff, so once the snappy processing is completed, the raster output is then transformed into a [COG (Cloud Optimized GeoTiff)](https://www.cogeo.org/) with extra lossless compression applied. With lossless compression applied (`COMPRESS=LZW, PREDICTOR=2`), the COG is half the size of the snappy output, but about 15-25% larger than the equivalent standard geotiff with the same compression flags applied.
The benefit of the format is that it is much faster to load for programs that properly understand it (QGIS, ArcGIS Pro, Rasterio, etc.), while still being backwards compatible with older software. My experience is that loading a standard 1-2GB Sentinel-1 raster into QGIS will take quite some time, whereas a COG will load almost immediatly, and will zoom, pan, and perform local histogram stretches MUCH faster.

## General Notes
The docker image is currently re-launched every time a file is needed to be processed. Experimenting with keeping it open to process everything did not yield a significant time saving, despite the small amount of overhead of launching snappy over and over again.
The largest reasons for this are:
- The overhead for launching snappy is relatively small compared with the processing time
- The processing time has a significant proportion spent processing supporting products from ESA (eg SRTM dems)
- These supporting data products do not seem to be re-used by snap within the same session, and need to be re-processed each time.

For these reasons, the processing is currently done per file, by:
1. Downloading a file
2. Processing that file with snappy
3. Post-processing that file
4. Moving to the next file

This was done to preserve modularity, and to more easily understand the progress of the program when processing a large number of files.

## Wishlist
Future steps to increase the perfomance of the program include:
- [ ] An option to merge nearby data products across boundaries for better viewing
- [X] Better checking for if a file has already been processed/etc
- [X] Quickstart guide for launching it on a fresh 22.04 Nimbus instance
- [ ] Pre-made Nimbus image with everything ready to go
- [ ] Script to create & remove cronjob (currently just manually done)

## Using the pre-made image
Unfortunately, this is not currently done yet.

## Manually setting up a NimbusVM
If for whatever reason you need to manually set up a nimubs VM, the steps are as follows:
1. Create an instance from the Ubuntu 22.04 image. When choosing a flavour, I recommend the 16 core version. Snappy and GDAL both benefit immensly from the extra cores and snappy in particular form the extra RAM. 40GB of storage is fine, we will make a data disk later. If you need help, see here: https://pawseysupercomputing.github.io/using-nimbus/06-launch-an-instance/index.html
2. ssh in and run `sudo apt update && sudo apt upgrade -y`
4. Once 2. finishes, reboot instance
3.Create a data volume, and attach it to the serverformat and mount volume as per https://pawseysupercomputing.github.io/using-nimbus/07-attaching-storage/index.html 
	1. I recommend mounting the file at /data. run `sudo mkdir /data`
	2. Once image is made and attached, find which one it is with `sudo fdisk -l` likely /dev/sdc or /dev/sdb. NB: There is a openstack bug where the name you give it may not be its true name.
	3. Once you know the device, if it is a fresh disk run (and be careful about typing this correctly) `sudo mkfs.ext4 /dev/sdb` if your device is /dev/sdb. If it is **NOT** a fresh disk, and already has a ext4 filesystem, and you do **NOT** want to purge everything on it, do not run this command
	4. run `sudo mount /dev/sdb /data`
	5. Set permissions properly for /data
 `sudo chown sudo chown ubuntu:ubuntu /data -R`
 	6. sudo chmod uog=rwX /data -R

5. install mambaforge, `wget https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-Linux-x86_64.sh`, then `bash Mambaforge-Linux-x86_64.sh`, follow instructions, install in default directory `/home/ubuntu/mambaforge`, then `yes` to init mambaforge (or run `conda init`)
6. activate mamba (exit & re-ssh, or try `source ~/.bashrc`)
7. Download the repo, using either of:
	- set up key pair and authenticate with github, then on nimbus run `git clone landgate`, 
	- or just download the zipfile, and from your own computer `scp landgate-main.zip ubuntu@0.0.0.0:/home/ubuntu/landgate.zip`, insterting your nimbus ip in place of `0.0.0.0`. Then back on nimbus run `sudo apt install unzip -y && unzip landgate.zip`
8. `cd landgate-main` or `cd landgate`
9. install packages needed. `pip install -r requirements.txt` and then `mamba install gdal`
10. build docker image, see instructions in `snappy_processing/README.md`, ie :
	1. `cd snappy_processing`
	2. Run the following build command. This can take a long time the first time it is run (about 10 minutes)
```
docker build -t landgate \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) .
```
	
11. `cd ..` to be back in the correct director (main code directory)
12. Edit the header of `main_config.py` as you need to. In particular, change your search parameters, and your data save location
13. Run `mkdir /data/S1_data`
14. Run `process_and_download.py` and bob's your uncle.

## References

1. https://github.com/mundialis/esa-snap/tree/master
2. https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
3. http://step.esa.int/docs/tutorials/tutorial_s1floodmapping.pdf
4. https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy

