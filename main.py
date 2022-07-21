#!/bin/env/python
"""
Description: Script for pre-processing S1 imagary.
Original Author: foad.farivar@curtin.edu.au
Creation Date: 2022-07-18
"""

import os
import gc
import logging
from snappy import ProductIO
from data.config import do_apply_orbit_file, do_speckle_filtering, do_calibration
from data.config import do_thermal_noise_removal, do_terrain_correction, do_grd_border_noise
from data.config import do_subset_from_polygon, do_subset_from_shapefile, write_file_format
from data.config import raw_data_path, final_data_path
from utils import apply_orbit_file, calibration, grd_border_noise, pre_checks, speckle_filtering, thermal_noise_removal

#configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def main():
    
    log.info("Checking fils and directories ...")
    pre_check = pre_checks()
    log.info("Pre-checks completed")

    raw_data_dir = os.path.join(os.getcwd(), raw_data_path)
    num_files = [f for f in os.listdir(raw_data_dir) if ".zip" in f]

    for file in num_files:
        gc.enable()
        gc.collect()

        log.info("processing {}".format(file))
        raw_product = ProductIO.readProduct(raw_data_dir + "\\" + file)

        #start pre-processing steps
        if do_apply_orbit_file:
            applied_orbit_product = apply_orbit_file (raw_product)
            log.info("apply orbit completed")

        if do_thermal_noise_removal:
            thermal_noise_removed_product = thermal_noise_removal(applied_orbit_product)
            log.info("thermal noise removal completed")

        if do_grd_border_noise:
            border_noise_removed_product = grd_border_noise(thermal_noise_removed_product)
            log.info("border noise removal completed")

        if do_calibration:
            calibreted_product = calibration(border_noise_removed_product)
            log.info("calibration completed")

        if do_speckle_filtering:
            despeckled_product = speckle_filtering(calibreted_product)
            log.info("de-speckling completed")

        

if __name__=='__main__':
    main()