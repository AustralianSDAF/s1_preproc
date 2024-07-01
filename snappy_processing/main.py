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
from os.path import join
import shutil
import gc
import logging
from snappy import ProductIO
import utils

import data.config as cfg

# DEM.srtm3GeoTiffDEM_HTTP = "http://download.esa.int/step/auxdata/dem/SRTM90/tiff/"
# configure logging
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Set flags for an issue with click/python conflict of ASCII encoding for environment
os.environ["LC_ALL"] = r"C.UTF-8"
os.environ["LANG"] = r"C.UTF-8"


@click.command()
@click.option("--filename", default=None)
@click.option("--filelist", default=None)
@click.option("--shapefile", default=None)
def main(filename, filelist, shapefile):
    """Helper function to separate cmdline usage from python importing"""
    process_file(filename, filelist, shapefile)


def process_file(filename=None, filelist=None, shapefile_path=None):
    """
    Process a single file, and update the filelist.

    Parameters
    ----------
    filename : str, optional
        The name of the file to be processed.
        One of filename or filelist should be given
    filelist : str, optional
        A text file that lists the filenames that will be used
        One of filename or filelist should be given
    shapefile_path : str, optional
        The path to the shapefile to be used

    Returns
    -------
    None

    """

    # Change config if arg present
    if shapefile_path is not None:
        cfg.do_subset_from_shapefile = True
        cfg.do_subset_from_polygon = False

    log.info(f"Filename passed in! Filename is {filename}")
    log.info("Checking files and directories ...")
    pre_check = utils.pre_checks(
        filename,
        filelist,
        cfg.raw_data_path,
        shapefile_path,
        cfg.do_subset_from_shapefile,
        cfg.final_data_path,
        cfg.archive_data_path,
        cfg.do_archive_data,
    )

    if pre_check == 1:
        log.info("Pre-checks completed")
    else:
        log.error("Pre-Checks failed. Terminating execution")
        return 0

    cfg.raw_data_dir = join(os.getcwd(), cfg.raw_data_path)
    if filelist is not None:
        log.info(f"Loading file list {filelist}")
        with open(filelist, "r") as f:
            file_list = [l.strip("\n") for l in f.readlines() if ".zip" in l]
        log.info("    \n".join(["Filelist loaded. Files to process are:", *file_list]))
    else:
        file_list = [
            f
            for f in os.listdir(cfg.raw_data_dir)
            if os.path.basename(f) == os.path.basename(filename)
        ]

    # Check if files are already processed.
    processed_check_dir = join(cfg.final_data_path, ".processed")
    os.makedirs(processed_check_dir, exist_ok=True)
    processed_files = os.listdir(processed_check_dir)
    num_files = len(file_list)
    for fname1 in map(os.path.basename, processed_files):
        for j, fname2 in enumerate(map(os.path.basename, file_list)):
            if fname1 == fname2:
                file_list.pop(num_files - j)

    log.info(file_list)
    for fname in file_list:
        if utils.check_file_processed(fname, cfg.final_data_path, zip_file_given=True):
            log.info("File already processed. Skipping.")
            continue
        # check if file exists
        gc.enable()
        gc.collect()
        full_fname = join(cfg.raw_data_dir, fname)
        log.info("processing {}".format(fname))
        raw_product = ProductIO.readProduct(join(cfg.raw_data_dir, full_fname))
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
            subsetted_product = utils.subset_from_shapefile(
                input_prod, shapefile_path=shapefile_path
            )
            log.info("subsetting form shapefile completed")
            input_prod = subsetted_product

        if cfg.do_thermal_noise_removal:
            thermal_noise_removed_product = utils.thermal_noise_removal(
                input_prod, cfg.thermal_noise_removal_param
            )
            log.info("thermal noise removal completed")
            input_prod = thermal_noise_removed_product

        if cfg.do_grd_border_noise:
            border_noise_removed_product = utils.grd_border_noise(
                input_prod, cfg.grd_border_noise_param
            )
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
            terrain_corrected_product = utils.terrain_correction(
                input_prod, cfg.terrain_correction_param
            )
            log.info("terrain correction completed")
            input_prod = terrain_corrected_product

        # writing final product
        processed_product_name = product_name + "_" + "processed"

        output_path = join(cfg.final_data_path, processed_product_name)
        output_data_dir = join(os.getcwd(), output_path)

        ProductIO.writeProduct(input_prod, output_data_dir, cfg.write_file_format)

        log.info("processed data saved in {}".format(output_data_dir))

        if cfg.do_archive_data:
            archive_data_dir = join(os.getcwd(), cfg.archive_data_path)
            shutil.move(cfg.raw_data_dir + "/" + fname, cfg.archive_data_dir + "/" + fname)

        # Set metadata indicating file has been processed
        utils.create_proc_metadata(fname, cfg.final_data_path, zip_file_given=True)


if __name__ == "__main__":
    main()
