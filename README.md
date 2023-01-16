# Landgate-ASDAF project
### Sentinel-1 image pre-processing pipeline
Author(s):
- Leigh Tyers (leigh.tyers@curtin.edu.au)
- Foad Farivar (foad.farivar@curtin.edu.au)

## Contents
- [Overview](#overview)
- [Setup (Docker)](#setup-steps-docker)
- [Setup (Conda)](#setup-steps-conda)
- [Directory structure](#directory-structure)
- [References](#references)
___

## Overview 
A python repository for automatically acquiring and processing Sentinel 1 imagery over Australia.

This package is composed of two parts, a processing tool and a downloading tool. The downloading tool requires python >= 3.7 , while the processing tool requires python==3.6 (as of writing, python 3.6 has been depreciated). This discrepency is solved by building a docker image for the processing tool, which is called from the overarching python 3.10 script.

## Downloading tool
TODO

## Processing tool
TODO

Snappy by default doesnt good compresion to the geotiff, so once the snappy processing is completed, the raster output is then transformed into a [COG (Cloud Optimized GeoTiff)](https://www.cogeo.org/) with extra compression applied. With lossless compression applied (`COMPRESSION=LZW, PREDICTOR=2`), the COG is half the size of the snappy output, but about 15-25% larger than the equivalent standard geotiff with the same compression flags applied.   
The benefit is a format that it is much faster to load for programs that properly understand it (QGIS, ArcGIS Pro, Rasterio etc), while still being backwards compatible with older software. My experience is that loading a standard 1-2GB raster into QGIS will take quite some time, whereas a COG will load almost immediatly, and will zoom, pan, and perform local histogram stretches MUCH faster.

## References

1. https://github.com/mundialis/esa-snap/tree/master
2. https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
3. http://step.esa.int/docs/tutorials/tutorial_s1floodmapping.pdf
4. https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy

