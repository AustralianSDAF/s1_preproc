# Landgate-ASDAF project
### Sentinel-1 image pre-processing pipeline
Author(s):
- Leigh Tyers (leigh.tyers@curtin.edu.au)
- Foad Farivar (foad.farivar@curtin.edu.au)

## Contents
- [Overview](#overview)
- [Downloading tool](#downloading-tool)
- [Processing tool](#processing-tool)
- [Notes](#notes)
- [References](#references)
___

## Overview 
A python repository for automatically acquiring and processing Sentinel 1 imagery over Australia.

This package is composed of two parts, a processing tool and a downloading tool. The downloading tool requires python >= 3.7 , while the processing tool requires python==3.6 (as of writing, python 3.6 has been depreciated). This discrepency is solved by building a docker image for the processing tool, which is called from the overarching python 3.10 script.

## Downloading tool
TODO

## Processing tool
### Snappy processing
The processing tool first uses snappy. As snappy requires python 3.6 (which is incompatible with the downloading tool, a docker image is built. See [snappy_processing/README.md](snappy_processing/README.md) for steps on how to set up the docker container. Docker should be included on the Nimbus ubuntnu 22.04 image.  

### GDAL Processing
Snappy by default doesnt apply adequate compresion to the geotiff, so once the snappy processing is completed, the raster output is then transformed into a [COG (Cloud Optimized GeoTiff)](https://www.cogeo.org/) with extra lossless compression applied. With lossless compression applied (`COMPRESS=LZW, PREDICTOR=2`), the COG is half the size of the snappy output, but about 15-25% larger than the equivalent standard geotiff with the same compression flags applied.   
The benefit of the format is that it is much faster to load for programs that properly understand it (QGIS, ArcGIS Pro, Rasterio, etc.), while still being backwards compatible with older software. My experience is that loading a standard 1-2GB Sentinel-1 raster into QGIS will take quite some time, whereas a COG will load almost immediatly, and will zoom, pan, and perform local histogram stretches MUCH faster.

## General Notes
The docker iamge is currently re-launched every time a file is needed to be processed. Experimenting with keeping it open to process everything did not yield a significant time saving, despite the small amount of overhead of launching snappy over and over again.
The largest reasons for this are:
- The overhead for launching snappy is relatively small compared with the processing time
- The processing time is has a significant proportion spent downloading supporting products from ESA (eg SRTM dems), even with a half gigabit connection.
- These supporting data products do not seem to be re-used by snap within the same session.

For these reasons, the processing is currently done per file, by:
1. Downloading a file
2. Processing that file with snappy
3. Post-processing that file
4. Moving to the next file

This was done to preserve modularity, and to more easily understand the progress of the program when processing a large number of files.

## TODO
Future steps to increase the perfomance of the program include:
- [ ] Having a separate thread to download and process files, such that something is always being downloaded at any given time. This would perhaps involve launching a thread after each product is downloaded to process the product. There may be some issues with snappy needing to download additional materials at the same time, but there would likely be time savings due to almost always having something being downloaded (and the downloading, even at the speeds nimbus achieves, being the limiting factor).
- [ ] An option to merge nearby data products across boundaries for better viewing
- [ ] Better checking for if a file has already been processed/etc

## References

1. https://github.com/mundialis/esa-snap/tree/master
2. https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface
3. http://step.esa.int/docs/tutorials/tutorial_s1floodmapping.pdf
4. https://github.com/wajuqi/Sentinel-1-preprocessing-using-Snappy

