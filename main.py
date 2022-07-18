#!/bin/env/python
"""
Description: Script for pre-processing S1 imagary.
Original Author: foad.farivar@curtin.edu.au
Creation Date: 2022-07-18
"""

import os
import logging

#from unicodedata import name


#configure logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def main():

    #reading config file parameters
    from data.config import do_apply_orbit_file


if __name__=='__main__':
    main()