#!/usr/bin/env python
"""
Description: Script for pre-processing S1 imagery.
             Due to compatibility issues between the download
             library and the processing library (snappy), we
             need to
Original Author: leigh.tyers@curtin.edu.au
Creation Date: 2023-01-13
"""
import logging
import click

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def run_docker_container(filename=None, file_list=None, data_directory='data', config_override=False, **kwargs):
    # Runs the docker container with appropriate cmdline arguments
    # Allows for data_directory to be passed
    # config_override will overwrite the config file if it exists
    from subprocess import Popen, PIPE, STDOUT
    import logging
    from os.path import join, isfile
    import shutil
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.info("Beggining logging...")


    def log_subprocess_output(pipe):
        for line in iter(pipe.readline, b''): # b'\n'-separated lines
            log.info(line)

    cmd = f"docker run --rm -v {os.path.abspath(data_directory)}/:/app/data landgate:0.3"

    if(file_list):
        cmd+=" --filelist 'data/files_to_process.txt'"
        # Santise files and output
        file_list = [os.path.basename(f) for f in file_list]
        with open(join(data_directory, 'files_to_process.txt'), 'w') as f:
            f.writelines('\n'.join(file_list))
    elif(filename):
        cmd+=f" --filename {filename}"
    else:
        raise ValueError("File_list and filename are not valid.")


    for key, val in kwargs.items():
        if key == 'shapefile':
            cmd += f"  --{key} '{join('data', os.path.basename(val))}'"
        else:
            cmd += f"  --{key} '{val}'"
    log.info(cmd)
    # Check if config file is in directory
    try:
        if((not isfile(join(data_directory, 'config.py'))) or config_override):
            os.makedirs(data_directory, exist_ok=True)
            shutil.copy(join(code_dir, 'data', 'config.py'), data_directory)
    except shutil.SameFileError:
        pass
    log.info(['-'*50])
    log.info([f'    Processing file {file}  '])
    process = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    with process.stdout:
        log_subprocess_output(process.stdout)

    exitcode = process.wait() # 0 means success
    if(not exitcode):
        log.info("    Exitcode 0, docker container success")
    else:
        log.error(f"    Exitcode nonzero for file: {file}")
        log.error(f"    Exitcode was: {exitcode}")


def write_shapefile(polygon, fpath = "data/search_polygon.shp", crs_num=4326):
    """ writes an ESRI shapefile from a shapely polygon using osgeo """
    from osgeo import ogr
    from osgeo import osr
    import os

    crs_num = int(crs_num)



    # Create a polygon from a ring (which we can assign points to)
    ring = None
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for coord in polygon.boundary.coords:
        ring.AddPoint(coord[0], coord[1])
        lastPoint = [coord[0], coord[1]]

    poly = ogr.Geometry(ogr.wkbPolygon)

    poly.AddGeometry(ring)

    # Set up the shapefile driver
    driver = ogr.GetDriverByName("ESRI Shapefile")

    # create the data source
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    ds = driver.CreateDataSource(fpath)

    # create the spatial reference system, WGS84
    srs =  osr.SpatialReference()
    srs.ImportFromEPSG(crs_num)

    # create one layer self
    layer = ds.CreateLayer("polygon", srs, ogr.wkbPolygon)

    # Add an ID field
    idField = ogr.FieldDefn("id", ogr.OFTInteger)
    layer.CreateField(idField)

    # Create the feature and set values
    featureDefn = layer.GetLayerDefn()
    feature = ogr.Feature(featureDefn)
    feature.SetGeometry(poly)
    feature.SetField("id", 1)
    layer.CreateFeature(feature)

    feature = None

    # Save and close DataSource
    ds = None

def reformat_geotif(input_fname, output_fname=None):
    """ Reformats a geotiff to be a COG with default options """
    from osgeo import gdal
    import re
    if output_fname is None:
        output_fname = re.sub('(.tif)$', '_cog.tif', input_fname)
    options=gdal.TranslateOptions(
        format = 'COG',
        noData=0,
        options=["-co","COMPRESS=LZW",
                 "-co","PREDICTOR=2",
                 "-co", "NUM_THREADS=ALL_CPUS", ]
    )
    d = gdal.Translate(output_fname, input_fname,
                   options=options)
    d = None
    return output_fname

def process_result(result, data_directory=data_directory, del_intermediate=True):
    import re
    from os.path import join, basename

    log.info("-"*20)
    log.info(f"Starting download for result {result.properties['title']}")
    fname = result.download(extract=False)

    final_data_path = join(data_directory, 'data_processed')
    fpath_proc = join(final_data_path, os.path.basename(fname))[:-4]+'_processed.tif'
    cog_fname = re.sub('(.tif)$', '_cog.tif', fpath_proc)

    if(check_file_processed(cog_fname, final_data_path, zip_file_given=False)):
        log.info(f'Skipping processing {cog_fname} as it already exists.')
        return

    log.info("-"*20)
    log.info(f"   Starting snappy processing for result {result.properties['title']}")
    run_docker_container(fname, data_directory=data_directory)

    log.info("-"*20)
    log.info(f"   Starting cog reformatting for result {result.properties['title']}")
    if(not os.path.isfile(fpath_proc)):
        log.error(f" File {fpath_proc} does not exist.")

    reformat_geotif(fpath_proc)
    create_proc_metadata(cog_fname, final_data_path, zip_file_given=False)
    if(del_intermediate):
        try:
            os.remove(fpath_proc)
            os.remove(join(data_directory, 'data_processed', '.processed', basename(fpath_proc)+'.done'))
        except ValueError:
            log.error('@'*10)
            log.error('Process likely failed at an earlier step, continuing')
            log.error('@'*10)

    log.info(f"All done for {result.properties['title']}")
    log.info("-"*20)
    return


def main():
    import os
    import logging
    code_dir = os.getcwd()

    data_directory = '/home/leight/LANDGATE/data/S1_data'
    raw_data_path = os.path.join(data_directory, 'data_raw')
    final_data_path = os.path.join(data_directory, 'data_processed')
    os.makedirs(raw_data_path, exist_ok=True)

    os.environ["EODAG__SARA__DOWNLOAD__OUTPUTS_PREFIX"] = os.path.abspath(raw_data_path)

    import getpass # Python password library

    os.environ["EODAG__SARA__AUTH__CREDENTIALS__USERNAME"] = input("Please enter your SARA username, then press ENTER (not SHIFT+ENTER)")
    os.environ["EODAG__SARA__AUTH__CREDENTIALS__PASSWORD"] = getpass.getpass("Enter your password for SARA then press enter (not SHIFT+ENTER)")

    from eodag import EODataAccessGateway
    from eodag import setup_logging

    setup_logging(verbose=2)

    dag = EODataAccessGateway()

    dag.set_preferred_provider("sara")

    # ---------------------------
    # TODO move search criteria to config file
    bounds = [116.29493,-20.55255, 117.77237,-21.55667]
    geo = {"lonmin": bounds[0], "latmin": bounds[1], "lonmax": bounds[2], "latmax": bounds[3]}

    search_criteria = {
        "productType": "S1_SAR_GRD",
        "start": "2021-01-20",
        "end": "2021-03-10",
        "sensorMode": "IW",
        "geom": geo
    }
    # ------------------------------------------------------

    search_results = dag.search_all(**search_criteria)

    for result in results:
        process_result(result)


if __name__ == __main__:
    # Load config & setup
    main()



