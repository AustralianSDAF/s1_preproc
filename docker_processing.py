#!/usr/bin/env python
"""
Description: library for calling docker from a python script
Original Author: leigh.tyers@curtin.edu.au
Creation Date: 2023-01-13
"""

import json
import logging
import os
from os.path import join, isfile
from pathlib import Path
from subprocess import PIPE, STDOUT
import shutil
import subprocess
import sys


from main_config import log_fname, data_directory, docker_image_name

log_fname = os.path.join(data_directory, log_fname)
log_fname = Path(log_fname).expanduser().resolve().as_posix()
os.makedirs(os.path.dirname(log_fname), exist_ok=True)
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler(log_fname), logging.StreamHandler(sys.stdout)],
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def docker_is_root():
    """
    Checks if the docker version on linux is a root install (not rootless) via a system call
    """
    try:
        text_output = subprocess.check_output("docker version | grep rootlesskit", shell=True)
    except:
        text_output = None
    is_root = False if (text_output) else True
    return is_root


def check_docker_image_exists(container_name: str) -> bool:
    """Checks if a docker image is in the local cache"""
    cmd = 'docker image list --filter "reference={container_name}" --format json'
    proc = subprocess.Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    std_out, err = proc.communicate()
    # output is a byte string so we need to decode it
    std_out_split = std_out.decode("utf-8").split("\n")
    images = [json.loads(line) for line in std_out_split if line]
    image_exists = any([image["Repository"] == container_name for image in images])
    log.info(f"Does docker image {container_name} exist: {image_exists}")
    return image_exists


def build_docker_container(container_name: str, location: str = "snappy_processing"):
    """Builds a docker container from a location"""
    base_path = sys.path[0]
    location_path_full = Path(base_path) / location
    log.info(f"Building docker container {container_name} from {location_path_full}")
    log.info("This can take up to 20+ minutes due to the SNAP installation")
    cmd = f"docker build {location_path_full} -t {container_name}"
    log.info(f"Running cmd '{cmd}'")
    proc = subprocess.Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    with proc.stdout:
        log_subprocess_output(proc.stdout, initial_text="Docker build ouput: ")
    proc.wait()
    return


def form_docker_command(
    run_dir, container_name="s1_preproc", filename=None, file_list=None, **kwargs
):
    """Forms the command to run docker

    See Also
    --------
    run_docker_container : Uses this function
    """
    cmd = f"docker run --rm -v {run_dir}/:/app/data "
    if docker_is_root():
        cmd += " --user $(id -u):$(id -g) "
    cmd += f" {container_name} "

    if file_list:
        cmd += " --filelist 'data/files_to_process.txt'"
        # Santise files and output
        file_list = [os.path.basename(f) for f in file_list]
        with open(join(data_directory, "files_to_process.txt"), "w") as f:
            f.writelines("\n".join(file_list))
    elif filename:
        cmd += f" --filename {filename}"
    else:
        raise ValueError("File_list and filename are not valid.")

    for key, val in kwargs.items():
        if key == "shapefile":
            cmd += f"  --{key} '{join('data', os.path.basename(val))}'"
        else:
            cmd += f"  --{key} '{val}'"

    return cmd


def log_subprocess_output(pipe, initial_text="Docker Output: ") -> None:
    # need to read output as bytes, so encode + concat then decode or a bug printing blank lines occurs. No idea why
    for line in iter(pipe.readline, b""):
        log.info((initial_text.encode() + line.rstrip()).decode())

    return


def run_docker_container(
    filename=None, file_list=None, data_directory="data", config_override=True, **kwargs
) -> None:
    """
    Runs the docker container with appropriate cmdline arguments

    Parameters
    ----------
    filename : str, optional
        The name of the file to be processed, either filename or file_list is required
    file_list : list, optional
        The list of files to be processed, either filename or file_list is required
    data_directory : str, optional
        The directory where the data is located, default is "data"
    config_override : bool, optional
        A flag to indicate if the config file should be overridden, default is False
    **kwargs:
        Additional command line arguments passed to the container

    Returns
    -------
    None

    """

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.info("Beggining logging...")

    run_dir = os.path.abspath(data_directory)

    image_name = docker_image_name
    image_exists = check_docker_image_exists(container_name=image_name)
    if not image_exists:
        build_docker_container(container_name=image_name)

    cmd = form_docker_command(
        run_dir=run_dir, container_name=image_name, filename=filename, file_list=file_list, **kwargs
    )
    log.info(f"Docker command is: {cmd}")
    # The docker image needs a local copy of config in the appropriate directory.
    code_dir = os.path.dirname(os.path.realpath(__file__))
    try:
        if (not isfile(join(data_directory, "config.py"))) or config_override:
            os.makedirs(data_directory, exist_ok=True)
            shutil.copy(join(code_dir, "main_config.py"), join(data_directory, "config.py"))
    except shutil.SameFileError:
        pass
    # move shapefile into relevat

    log.info(["-" * 50])
    log.info([f"    Processing file {filename}  "])
    process = subprocess.Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        log_subprocess_output(process.stdout)

    exitcode = process.wait()  # 0 means success
    if not exitcode:
        log.info("    Exitcode 0, docker container success")
    else:
        log.error(f"    Exitcode nonzero for file: {filename}")
        log.error(f"    Exitcode was: {exitcode}")
    return
