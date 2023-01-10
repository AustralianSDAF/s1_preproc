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
import utils

import data.config as cfg

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
    """Helper function to separate cmdline usage from python importing"""
    process_file(filename, shapefile)


def process_file(filename, shapefile=None):
    """Processes a file using input filename. If filename is None it tries to get files from a directory"""
    # Load polygon from file
    if(shapefile is not None):
        shapefile_path = shapefile
        cfg.do_subset_from_shapefile = True
        cfg.do_subset_from_polygon = False

    log.info(f"Filename passed in! Filename is {filename}")
    log.info("Checking files and directories ...")
    pre_check = utils.pre_checks(
        filename,
        cfg.raw_data_path,
        shapefile_path,
        cfg.do_subset_from_shapefile,
        cfg.final_data_path,
        cfg.archive_data_path,
        cfg.do_archive_data
    )

    if pre_check == 1:
        log.info("Pre-checks completed")
    else:
        log.error("terminating execution")
        return 0

    cfg.raw_data_dir = os.path.join(os.getcwd(), cfg.raw_data_path)
    if(filename is None):
        num_files = [f for f in os.listdir(cfg.raw_data_dir) if ".zip" in f]
    else:
        num_files = [f for f in os.listdir(cfg.raw_data_dir) if os.path.basename(f) == os.path.basename(filename)]
    log.info(num_files)
    for file in num_files:
        gc.enable()
        gc.collect()
        full_fname = os.path.join(cfg.raw_data_dir, file)
        log.info("processing {}".format(file))
        raw_product = ProductIO.readProduct(os.path.join(cfg.raw_data_dir, full_fname))
        product_name = raw_product.getName()
        input_prod = raw_product

        # start pre-processing steps
        if cfg.do_apply_orbit_file:
            applied_orbit_product = utils.apply_orbit_file(input_prod, cfg.apply_orbit_file_param)
            log.info("apply orbit completed")
            input_prod = applied_orbit_product

        if cfg.do_subset_from_polygon:
            subsetted_product = utils.subset_from_polygon(input_prod, shpfile=cfg.polygon_param)
            log.info("subsetting form polygon completed")
            input_prod = subsetted_product
        elif cfg.do_subset_from_shapefile:
            subsetted_product = utils.subset_from_shapefile(input_prod, shapefile_path=shapefile_path)
            log.info("subsetting form shapefile completed")
            input_prod = subsetted_product

        if cfg.do_thermal_noise_removal:
            thermal_noise_removed_product = utils.thermal_noise_removal(input_prod, cfg.thermal_noise_removal_param)
            log.info("thermal noise removal completed")
            input_prod = thermal_noise_removed_product

        if cfg.do_grd_border_noise:
            border_noise_removed_product = utils.grd_border_noise(input_prod, cfg.grd_border_noise_param)
            log.info("border noise removal completed")
            input_prod = border_noise_removed_product

        if cfg.do_calibration:
            calibreted_product = utils.calibration(input_prod, cfg.calibration_param)
            log.info("calibration completed")
            input_prod = calibreted_product

        if cfg.do_speckle_filtering:
            despeckled_product = utils.speckle_filtering(input_prod, cfg.speckle_filtering_param)
            log.info("de-speckling completed")
            input_prod = despeckled_product

        if cfg.do_terrain_correction:
            terrain_corrected_product = utils.terrain_correction(input_prod, cfg.terrain_correction_param)
            log.info("terrain correction completed")
            input_prod = terrain_corrected_product

        # writing final product
        processed_product_name = product_name + "_" + "processed"

        output_path = os.path.join(cfg.final_data_path, processed_product_name)
        output_data_dir = os.path.join(os.getcwd(), output_path)

        ProductIO.writeProduct(input_prod, output_data_dir, cfg.write_file_format)

        log.info("processed data saved in {}".format(output_data_dir))

        if cfg.do_archive_data:
            archive_data_dir = os.path.join(os.getcwd(), cfg.archive_data_path)
            shutil.move(cfg.raw_data_dir + "/" + file, cfg.archive_data_dir + "/" + file)


if __name__ == '__main__':
    main()
