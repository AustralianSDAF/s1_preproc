#!/usr/bin/env python

'''
Main script for Sentinel-1 Product Downloading, Pre-checking and InSAR Processing.
Allows individual and batch processing based on input from config.py.

Author: Calvin Pang (calvin.pang@curtin.edu.au)
'''

from pathlib import Path
import subprocess

from downloader import run_all
from pre_check import insar_precheck
from processing import insar_processing

from config import work_dir, search_criteria, from_precheck
from src.downloader_config import download_from_thredds, del_intermediate

def batch_insar_processing() -> None:
    '''
    Function to perform batch InSAR processing by reading in the results
    from the pre-check output file.
    
    You may encounter memory issues if you don't run each Sentinel-1 Processing as a subprocess
    https://forum.step.esa.int/t/snappy-doesnt-clear-memory-cache/8284/17
    '''
    with open(file=Path(work_dir, "precheck_output.csv"), mode="r", encoding="UTF-8") as f:
        processing_pairs = f.readlines()[1:]
        for pair in processing_pairs:
            product_1 = pair.split(',')[0]
            product_2 = (pair.split(',')[1])
            # insar_processing(filename_1=product_1, filename_2=product_2)
            subprocess.run(['python', 'processing.py', product_1, product_2], check=False)

def main() -> None:
    '''
    Function to complete download, precheck and processing of products as configured from config files.
    Args:
        None
    Returns:
        None
    '''
# Download Products
    Path(work_dir).mkdir(exist_ok=True, parents=True)
    
    print('=====DOWNLOADING=====\n')
    run_all(
        download_from_thredds=download_from_thredds,
        data_directory=work_dir,
        search_criteria=search_criteria,
        del_intermediate=del_intermediate,
    )
    # Perform Precheck
    print('=====PRE-SCREENING=====\n')
    insar_precheck()
    
    # Perform InSAR Processing
    print('=====PROCESSING=====\n')
    if from_precheck is False:
        insar_processing()
    else:
        batch_insar_processing()

if __name__ == "__main__":
    main()

