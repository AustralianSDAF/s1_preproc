#!/bin/env/python
"""
Description: Script for pre-processing S1 imagary.
Original Author: foad.farivar@curtin.edu.au
Edited by: leigh.tyers@curtin.edu.au
Creation Date: 2022-07-28
"""
import sys

# No need to include this line if running on Docker
# sys.path.append('/root/.snap/snap-python')

import click
import os
import shutil
import gc
import logging
from snappy import ProductIO
from data.config import do_apply_orbit_file, do_speckle_filtering, do_calibration
from data.config import do_thermal_noise_removal, do_terrain_correction, do_grd_border_noise
from data.config import do_subset_from_polygon, do_subset_from_shapefile, write_file_format
from data.config import raw_data_path, final_data_path, archive_data_path, do_archive_data
from utils import apply_orbit_file, calibration, grd_border_noise, pre_checks, speckle_filtering, terrain_correction
from utils import subset_from_polygon, subset_from_shapefile, thermal_noise_removal, write_file

# DEM.srtm3GeoTiffDEM_HTTP = "http://download.esa.int/step/auxdata/dem/SRTM90/tiff/"
# configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Set flags for an issue with click/python conflict of ASCII encoding for environment
os.environ['LC_ALL'] = r'C.UTF-8'
os.environ['LANG'] = r'C.UTF-8'



@click.command()
@click.option('--filename', default=None)
@click.option('--shapefile', default=None)
def main(filename, shapefile):
    log.info(f"Filename passed in! Filename is {filename}")
    log.info("Checking files and directories ...")
    pre_check = pre_checks(filename)
    # Load polygon from file
    if(shapefile is not None):
        shapefile_path = shapefile
        do_subset_from_shapefile = True
        do_subset_from_polygon = False

    if pre_check == 1:
        log.info("Pre-checks completed")
    else:
        log.error("terminating execution")
        return 0

    raw_data_dir = os.path.join(os.getcwd(), raw_data_path)
    if(filename is None):
        num_files = [f for f in os.listdir(raw_data_dir) if ".zip" in f]
    else:
        num_files = [f for f in os.listdir(raw_data_dir) if os.path.basename(f) == os.path.basename(filename)]
    log.info(num_files)
    for file in num_files:
        gc.enable()
        gc.collect()
        full_fname = os.path.join(raw_data_dir, file)
        log.info("processing {}".format(file))
        raw_product = ProductIO.readProduct(os.path.join(raw_data_dir, full_fname))
        product_name = raw_product.getName()
        input_prod = raw_product

        # start pre-processing steps
        if do_apply_orbit_file:
            applied_orbit_product = apply_orbit_file(input_prod)
            log.info("apply orbit completed")
            input_prod = applied_orbit_product

        if do_subset_from_polygon:
            subsetted_product = subset_from_polygon(input_prod)
            log.info("subsetting form polygon completed")
            input_prod = subsetted_product
        elif do_subset_from_shapefile:
            subsetted_product = subset_from_shapefile(input_prod)
            log.info("subsetting form shapefile completed")
            input_prod = subsetted_product

        if do_thermal_noise_removal:
            thermal_noise_removed_product = thermal_noise_removal(input_prod)
            log.info("thermal noise removal completed")
            input_prod = thermal_noise_removed_product

        if do_grd_border_noise:
            border_noise_removed_product = grd_border_noise(input_prod)
            log.info("border noise removal completed")
            input_prod = border_noise_removed_product

        if do_calibration:
            calibreted_product = calibration(input_prod)
            log.info("calibration completed")
            input_prod = calibreted_product

        if do_speckle_filtering:
            despeckled_product = speckle_filtering(input_prod)
            log.info("de-speckling completed")
            input_prod = despeckled_product

        if do_terrain_correction:
            terrain_corrected_product = terrain_correction(input_prod)
            log.info("terrain correction completed")
            input_prod = terrain_corrected_product

        # writing final product
        processed_product_name = product_name + "_" + "processed"

        output_path = os.path.join(final_data_path, processed_product_name)
        output_data_dir = os.path.join(os.getcwd(), output_path)
        # write_file(input_prod, output_data_dir)

        ProductIO.writeProduct(input_prod, output_data_dir, write_file_format)

        log.info("processed data saved in {}".format(output_data_dir))

        if do_archive_data:
            archive_data_dir = os.path.join(os.getcwd(), archive_data_path)
            shutil.move(raw_data_dir + "/" + file, archive_data_dir + "/" + file)

if __name__=='__main__':
    main()
