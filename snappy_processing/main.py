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
from pathlib import Path

import data.config as cfg
import orbits

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


# TODO make config file a cmdline input
@click.command()
@click.option("--filename", default=None)
@click.option("--filelist", default=None)
def main(filename, filelist):
    """Helper function to separate cmdline usage from python importing"""
    process_file(filename, filelist)


def process_file(filename=None, filelist=None):
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

    log.info(f"Filename passed in! Filename is {filename}")
    log.info("Checking files and directories ...")
    pre_check = utils.pre_checks(
        filename,
        filelist,
        cfg.raw_data_path,
        cfg.s1tbx_operator_order,
        cfg.final_data_path,
        cfg.archive_data_path,
        cfg.do_archive_data,
        cfg.shapefile_subdirectory,
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
        # Hardcoding garbage collection at max (2) to stop memory leaks
        gc.enable()
        gc.collect()
        full_fname = join(cfg.raw_data_dir, fname)
        log.info("processing {}".format(fname))
        input_prod = ProductIO.readProduct(join(cfg.raw_data_dir, full_fname))
        product_name = input_prod.getName()

        # Snap9's api is broken so we need to download orbitfiles seperately. Look to see if one exists
        # We dont need to pass this in later, we just need to move them to a specific (local) directory
        orbits.get_orbit_files(input_prod.getName(), aux_path=cfg.aux_location)

        all_parameters = cfg.s1tbx_operator_order

        # Adjust subsetting parameters to what's expected
        for i, operator_config in enumerate(all_parameters):
            if "shapefilePath" in operator_config:
                all_parameters[i] = utils.prepare_shapefile_subset(
                    operator_config, input_prod, cfg.polygon_subdirectory
                )
            elif "polygon" in operator_config:
                all_parameters[i] = utils.prepare_polygon_subset(operator_config)

        # Apply all other operators
        for operator_config in all_parameters:
            log.info(f"Applying operator '{operator_config['operatorName']}'")
            input_prod = utils.apply_generic_operator(input_prod, operator_config)

        # writing final product
        processed_product_name = product_name + "_" + "processed"

        output_path = Path(cfg.final_data_path) / processed_product_name
        output_data_dir = output_path.expanduser().resolve().as_posix()

        ProductIO.writeProduct(input_prod, output_data_dir, cfg.write_file_format)

        log.info("processed data saved in {}".format(output_data_dir))

        if cfg.do_archive_data:
            archive_data_dir = join(os.getcwd(), cfg.archive_data_path)
            shutil.move(cfg.raw_data_dir + "/" + fname, cfg.archive_data_dir + "/" + fname)

        # Set metadata indicating file has been processed
        utils.create_proc_metadata(fname, cfg.final_data_path, zip_file_given=True)


if __name__ == "__main__":
    main()
