#!/bin/env python# -*- coding: utf-8 -*-
#
# Functions for downloading products without EODAG (ie to do so from THREDDS)
#
# ===========================================================
#
# This file is partly derived from the EODAG project
#     https://www.github.com/CS-SI/EODAG
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
from main_config import log_fname
import sys
import os

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_fname),
        logging.StreamHandler(sys.stdout)
    ],
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)


def get_fpath(product, raw_data_path):
    """
    Given an eodag product object, returns the filepath of the file to be downloaded, mimics the naming of the file from EODAG

    Parameters
    ----------
    product : eodag.api.product.EOProduct
        EODAG product object
    raw_data_path : str
        The filepath to the directory where the raw data is stored

    Returns
    -------
    str
        The filepath of the raw product
    """
    from eodag.utils import sanitize
    from os.path import join
    # Create fname
    outputs_extension = '.zip'
    sanitized_title = sanitize(product.properties["title"])
    if sanitized_title == product.properties["title"]:
        collision_avoidance_suffix = ""
    else:
        collision_avoidance_suffix = "-" + sanitize(product.properties["id"])
    fs_path = os.path.join(
        raw_data_path,
        f"{sanitize(product.properties['title'])}{collision_avoidance_suffix}{outputs_extension}",
    )
    fs_path = os.path.join(
        raw_data_path,
        f"{sanitize(product.properties['title'])}{collision_avoidance_suffix}{outputs_extension}",
    )
    return fs_path


def declare_downloaded(product, raw_data_path):
    """
    Declares a product as downloaded by creating a .done file in the raw data path directory.
    The file name is the product's name + '.done', in the folder '.downloaded' relative to the original file
    Will mimic EODAGs syntax, by using the hash of the original download link (which will be re-created)

    Parameters
    ----------
    product : eodag.api.product.EOProduct
        an EODAG product object
    raw_data_path : str
        The directory where the raw data is stored

    Returns
    -------
    None
    """
    import hashlib
    import os
    from os.path import join
    download_records_dir = os.path.join(raw_data_path, ".downloaded")
    try:
        os.makedirs(download_records_dir)
    except OSError as exc:
        import errno
        if exc.errno != errno.EEXIST:  # Skip error if dir exists
            import traceback as tb
            log.warning(
                f"Unable to create records directory. Got:\n{tb.format_exc()}",
            )
    eodag_url = product.remote_location
    url_hash = hashlib.md5(eodag_url.encode("utf-8")).hexdigest()
    record_filename = os.path.join(download_records_dir, url_hash)
    try:
        with open(record_filename, 'w') as f:
            f.writelines(eodag_url)
    except OSError as e:
        log.exception(f"Unable to create file indicating download for {record_fname}. exception:")
    return True


def download_product_thredds(product, raw_data_path):
    """
    A custom downloader for when download_from_thredds=True. Will check if a file has already been downloaded

    Parameters
    ----------
    product : eodag.api.product.EOProduct
        an EODAG product object
    raw_data_path : str
        The path to the directory where the downloaded product will be saved.

    Returns
    -------
    None
    """
    from eodag.utils import ProgressCallback
    import requests
    fs_path = get_fpath(product, raw_data_path)
    if(product_downloaded(product, raw_data_path)):
        log.info(f"Product already downloaded: {fs_path}")
        return fs_path

    thredds_base_url = "https://dapds00.nci.org.au/thredds/fileServer/fj7/Copernicus/"
    threds_url = '/'.join(
        [thredds_base_url, *product.properties['quicklook'].split('/')[4:]]
    )[:-4] + '.zip'
    progress_callback = ProgressCallback(mininterval=0.1)
    progress_callback.desc = str(product.properties.get("id", ""))
    stream = requests.get(threds_url, stream=True)
    total =  int(stream.headers['content-length'])
    progress_callback.reset(total=total)
    with open(fs_path, "wb") as fhandle:
        for chunk in stream.iter_content(chunk_size=64*1024):
            size = fhandle.write(chunk)
            progress_callback.update(size)
    declare_downloaded(product, raw_data_path)
    return fs_path


def product_downloaded(product, raw_data_path):
    """
    Check if a product has already been downloaded

    Parameters
    ----------
    product : eodag.api.product.EOProduct
        The product to check if it has been downloaded
    raw_data_path : str
        The path where the raw data is stored

    Returns
    -------
    bool
        Whether or not the product has already been downloaded
    """
    import hashlib
    import os
    from os.path import join
    eodag_url = product.remote_location
    url_hash = hashlib.md5(eodag_url.encode("utf-8")).hexdigest()
    return os.path.isfile(join(raw_data_path, '.downloaded', url_hash))



if __name__ == "__main__":
    pass

