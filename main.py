#!/bin/env/python
"""
Description: Script for pre-processing S1 imagary.
Original Author: foad.farivar@curtin.edu.au
Creation Date: 2022-07-28
"""

import os
import gc
import logging
from snappy import ProductIO
from data.config import do_apply_orbit_file, do_speckle_filtering, do_calibration
from data.config import do_thermal_noise_removal, do_terrain_correction, do_grd_border_noise
from data.config import do_subset_from_polygon, do_subset_from_shapefile, write_file_format
from data.config import raw_data_path, final_data_path
from utils import apply_orbit_file, calibration, grd_border_noise, pre_checks, speckle_filtering, terrain_correction
from utils import subset_from_polygon, subset_from_shapefile, thermal_noise_removal, write_file

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
    if pre_check == 1:
        log.info("Pre-checks completed")
    else:
        log.error("terminating execution")
        return 0

    raw_data_dir = os.path.join(os.getcwd(), raw_data_path)
    num_files = [f for f in os.listdir(raw_data_dir) if ".zip" in f]

    for file in num_files:
        gc.enable()
        gc.collect()

        log.info("processing {}".format(file))
        raw_product = ProductIO.readProduct(raw_data_dir + "\\" + file)
        product_name = raw_product.getName()
        input_prod = raw_product
        
        #start pre-processing steps
        if do_apply_orbit_file:
            applied_orbit_product = apply_orbit_file (input_prod)
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
        write_file(input_prod, output_path)
        log.info("processed data saved in {output_path}".format(output_path))

        
if __name__=='__main__':
    main()