import subprocess
import time
from pathlib import Path

import snappy
from snappy import ProductIO, HashMap, GPF, ProductUtils, ProgressMonitor


def read_products(filepath_1: Path, filepath_2: Path) -> tuple[object, object]:
    """
    Reads in a pair of Sentinel-1 Products using SNAP.

        Args:
            filepath_1 (Path): Filepath for the first Sentinel-1 Product (Older)
            filepath_2 (Path): Filepath of the second Sentinel-1 Product (Newer)
        Returns:
            read_1 (org.esa.snap.core.datamodel.Product): First Sentinel-1 Product (Older)
            read_2 (org.esa.snap.core.datamodel.Product): Second Sentinel-1 Product (Newer)
    """
    product_1 = ProductIO.readProduct(str(filepath_1))
    product_2 = ProductIO.readProduct(str(filepath_2))

    return product_1, product_2


def insar_stack_overview(product_1: object, product_2: object) -> tuple[float, float]:
    """
    Calculates the baseline information of a product pair using the INSAR Stack Overview Operator
    within SNAP.
        Args:
            product_1 (org.esa.snap.core.datamodel.Product): First Sentinel-1 Product (Older)
            product_2 (org.esa.snap.core.datamodel.Product): Second Sentinel-1 Product (Newer)
        Returns:
            perpendicular_baseline (float): Distance between the satellites' position at the time of acquisition.
            temporal_baseline (float): Time between the first and second image in days.
    """
    # Instantiating the INSAR Stack Overview Operator
    InSarStackOverview = snappy.jpy.get_type(
        "org.esa.s1tbx.insar.gpf.InSARStackOverview"
    )

    # Creating the Sentinel-1 Product Stack
    insar_stack = snappy.jpy.array("org.esa.snap.core.datamodel.Product", 2)
    insar_stack[0] = product_1
    insar_stack[1] = product_2

    # Retrieving Results
    results = InSarStackOverview.calculateInSAROverview(insar_stack)
    result = results[1].getMasterSlave()
    perpendicular_baseline = result[0].getPerpendicularBaseline()
    temporal_baseline = result[0].getTemporalBaseline()

    return perpendicular_baseline, temporal_baseline


def topsar_split(
    product: object, subswath: str, first_burst: int, last_burst: int
) -> object:
    """
    Applies the TOPSAR Split Operator within SNAP to select only the bursts corresponding to the area of interest.
    Args:
        product (org.esa.snap.core.datamodel.Product): Sentinel-1 Product
        subswath (str): The subswath of insterest. Allowed values:  "IW1", "IW2" or "IW3"
        first_burst (int): The first burst index
        last_burst (int): The last burst index
    Returns:
        Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    allowed_subswaths = ["IW1", "IW2", "IW3"]
    if subswath not in allowed_subswaths:
        raise ValueError(
            f"Invalid subswath '{subswath}'. Allowed values: {allowed_subswaths}"
        )

    parameters = HashMap()
    parameters.put("subswath", subswath)
    parameters.put("selectedPolarisations", "VV")
    parameters.put("firstBurstIndex", first_burst)
    parameters.put("lastBurstIndex", last_burst)

    return GPF.createProduct("TOPSAR-Split", parameters, product)


def apply_orbit_file(product: object):
    """
    Applies a Precise Orbit File to the metadata of a Sentinel-1 Product using SNAP.
    Args:
        product (org.esa.snap.core.datamodel.Product): TOPSAR Split Product
    Returns:
        Orbit Applied Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()
    parameters.put("orbitType", "Sentinel Precise (Auto Download)")
    parameters.put("polyDegree", 3)

    return GPF.createProduct("Apply-Orbit-File", parameters, product)


def back_geocoding(product_1: object, product_2: object) -> object:
    """
    Applies the Back-Geocoding Operator to coregister a pair Sentinel-1 Products using SNAP.
    Args:
        product_1 (org.esa.snap.core.datamodel.Product): Orbit Applied First Sentinel-1 Product (Older)
        product_2 (org.esa.snap.core.datamodel.Product): Orbit Applied Second Sentinel-1 Product (Newer)
    Returns:
        Back-Geocoded Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()
    parameters.put("demName", "SRTM 1Sec HGT")
    products = [product_1, product_2]

    return GPF.createProduct("Back-Geocoding", parameters, products)


def enhanced_spectral_diversity(product: object) -> object:
    """
    Applies the Enhanced Spectral Diversity Operator within SNAP
    to increase the quality of coregistration.
    Args:
        product (org.esa.snap.core.datamodel.Product): Back-Geocoded Sentinel-1 Product
    Returns:
        Enhanced Spectral Diversity Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()

    return GPF.createProduct("Enhanced-Spectral-Diversity", parameters, product)


def write_esd_rgb_image(product: object, filename: Path):
    """
    Generates an RGB image (.png) of the coregistered reference and secondary product
    to show whether the images are correctly alligned.
    NOTE: This may take a while as processing is performed lazily.
    Args:
        product (org.esa.snap.core.datamodel.Product): Enhanced Spectral Diversity Sentinel-1 Product
        filename (Path): Filename of the RGB Product
    """
    # Retrieving the Required Bands from the ESD Sentinel-1 Product
    band_names = list(product.getBandNames())
    for band_name in band_names:
        if "Intensity" in band_name:
            if "VV_mst" in band_name:
                mst = band_name
            elif "VV_slv" in band_name:
                slv = band_name

    if mst and slv:
        _write_esd_rgb_image(product, mst, slv, filename)


def _write_esd_rgb_image(product: object, mst: str, slv: str, filename: Path):
    """
    Private method for write_esd_rgb_image()
    """
    # Sets RGB Bands for Image
    bands = [product.getBand(mst), product.getBand(mst), product.getBand(slv)]

    # Java Type Definitions required for Image Generation
    ImageManager = snappy.jpy.get_type("org.esa.snap.core.image.ImageManager")
    JAI = snappy.jpy.get_type("javax.media.jai.JAI")

    # Disabling JAI native MediaLib extensions
    System = snappy.jpy.get_type("java.lang.System")
    System.setProperty("com.sun.media.jai.disableMediaLib", "true")

    # Writing the Image
    image_info = ProductUtils.createImageInfo(bands, True, ProgressMonitor.NULL)
    image = ImageManager.getInstance().createColoredBandImage(bands, image_info, 0)
    JAI.create("filestore", image, str(filename), "PNG")


def interferogram(product: object, subtract_topographic_phase: bool) -> object:
    """
    Applies the Interferogram Operator within on a coregistered Sentinel-1 Product pair
    to produce the interferometric phase and coherence bands.
    Args:
        product (org.esa.snap.core.datamodel.Product): Enhanced Spectral Diversity Sentinel-1 Product
        subtractTopographicPhase (bool): TRUE for Displacement
                                        FALSE for Elevation processing.
    Returns:
        Interferogram Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()
    parameters.put("subtractFlatEarthPhase", True)
    parameters.put("subtractTopographicPhase", subtract_topographic_phase)
    parameters.put("includeCoherence", True)

    if subtract_topographic_phase:
        parameters.put("dem", "SRTM 1Sec HGT")

    return GPF.createProduct("Interferogram", parameters, product)


def tops_deburst(product: object) -> object:
    """
    Applies the TOPS Deburst Operator within SNAP on the interferogram product to remove seamlines between single bursts.
    Args:
        product (org.esa.snap.core.datamodel.Product): Interferogram Sentinel-1 Product
    Returns:
        TOPS Debursted Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()

    return GPF.createProduct("TOPSAR-Deburst", parameters, product)


def goldstein_phase_filtering(product: object) -> object:
    """
    Applies the Goldstein Phase Filtering Operator within SNAP to increase quality
    of the fringes in the interferogram.
    Args:
        product (org.esa.snap.core.datamodel.Product): TOPS Debursted Sentinel-1 Product
    Returns:
        Goldstein Phase Filtered Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()

    return GPF.createProduct("GoldsteinPhaseFiltering", parameters, product)


def multilooking(product: object) -> object:
    """
    Applies the Multi-Looking Operator within SNAP for optimal unwrapping results.
    Args:
        product (org.esa.snap.core.datamodel.Product): Goldstein Phase Filtered Sentinel-1 Product
    Returns:
        Multilooked Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    parameters = HashMap()

    return GPF.createProduct("Multilook", parameters, product)


def write_product(product, filepath: Path, fileformat: str = "BEAM-DIMAP"):
    """
    Performs SNAP processing and saves the processed Sentinel-1 Product in the specified
    file format.
    Note: This may take a while as all processing is performed lazily.
    Args:
        product (org.esa.snap.core.datamodel.Product): Sentinel-1 Product
        filepath (Path): Path to the saved Sentinel-1 Product
        fileformat (str): Format to save the Sentinel-1 Product. Allowed Values: 'BEAM-DIMAP', 'GeoTIFF' (Defaults to BEAM-DIMAP)
    """
    if fileformat not in ["BEAM-DIMAP", "GeoTIFF"]:
        raise ValueError(
            f"Invalid file format: {fileformat}. Allowed values are 'BEAM-DIMAP' and 'GeoTIFF'."
        )

    start_time = time.time()

    ProductIO.writeProduct(product, str(filepath), fileformat)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f'Successfully saved: "{filepath}"')
    if elapsed_time < 60:
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
    else:
        print(f"Completed in {elapsed_time/60:.2f} minutes")


def snaphu_export(
    product,
    targetfolder: Path,
    statcostmode: str,
    initmethod: str = "MCF",
    numprocessors: int = 8,
):
    """
    Calls the SNAPHU Export operator to conver the interferogram (as the wrapped phase)
    into a format which can be read by SNAPHU.
    NOTE: Known issue with SNAP 8/9 where SNAPHU Export does not work within SNAPPY.
    https://forum.step.esa.int/t/snaphu-export-in-snap-8-rises-indexoutofboundsexception/29278
    Current Workaround: Required to fall back to SNAP 7 or use SNAP GPT.
    Args:
        product (org.esa.snap.core.datamodel.Product): Pre-processed Sentinel-1 Product
        targetfolder (Path): Target directory to store the SNAPHU Export
        statcostmode (str): Select 'TOPO' for Digital Elevation Model or 'DEFO' for Displacement
        initmethod (str): Select 'MCF' or 'MST'. Defaults to 'MCF"
        numprocessoers (int): Defaults to 8 processors
    """
    parameters = HashMap()
    parameters.put("targetFolder", str(targetfolder))
    parameters.put("statCostMode", statcostmode)
    parameters.put("initMethod", initmethod)
    parameters.put("numberOfProcessors", numprocessors)
    parameters.put("rowOverlap", 200)
    parameters.put("colOverlap", 200)

    output = GPF.createProduct("SnaphuExport", parameters, product)
    ProductIO.writeProduct(output, str(targetfolder), "Snaphu")
    print(f'Successfully exported: "{targetfolder}"')


def snaphu_export_gpt(
    filepath: Path,
    targetfolder: Path,
    statcostmode: str,
    initmethod: str = "MCF",
    numprocessors: int = 8,
):
    """
    Converts the interferogram (as the wrapped phase) into a format
    which can be read by SNAPHU using GPT.
    Args:
        filepath (Path): Path to the saved preprocessed BEAM-DIMAP file.
        targetfolder (Path): Path to the target folder to save the SNAPHU Export.
        statcostmode (str): Select 'TOPO' for Digital Elevation Model or 'DEFO' for Displacement.
        initmethod (str): Select 'MCF' or 'MST'. Defaults to 'MCF"
        numprocessors (int): Defaults to 8 processors
    """
    return subprocess.run(
        [
            "gpt",
            "SnaphuExport",
            f"-Ssource={str(filepath)}",
            f"-PstatCostMode={statcostmode}",
            f"-PinitMethod={initmethod}",
            f"-PnumberOfProcessors={numprocessors}",
            f"-PtargetFolder={str(targetfolder)}",
        ],
        check=True,
    )


def snaphu_unwrapping(filepath: Path) -> object:
    """
    Calls SNAPHU to perform Phase Unwrapping SNAPHU Exported Sentinel-1 Product.
    Args:
        filepath (Path): Path to the SNAPHU Exported directory.
    """
    with open(Path(filepath, "snaphu.conf"), encoding="UTF-8") as f:
        cmd = f.readlines()[6][8:]

    return subprocess.run(cmd.split(), cwd=str(filepath), check=True)


def snaphu_import(preprocessed_product: object, snaphu_export_path: Path) -> object:
    """
    Imports the Unwrapped Phase and converts it back into the BEAM-DIMAP format
    with the required metadata from the Wrapped Phase product.
    Args:
        preprocessed_product (org.esa.snap.core.datamodel.Product): Pre-processed Sentine-1 Product
        snaphu_export_path: Path to the SNAPHU Unwrapped Product
    Returns:
        SNAPHU Imported Sentinel-1 Product (org.esa.snap.core.datamodel.Product)
    """
    unwrapped_hdr_path = list(snaphu_export_path.glob("UnwPhase_*VV*.hdr"))[0]
    unwrapped_product = snappy.ProductIO.readProduct(str(unwrapped_hdr_path))

    parameters = HashMap()
    products = [preprocessed_product, unwrapped_product]
    return GPF.createProduct("SnaphuImport", parameters, products)


def phase_to_displacement(product: object):
    """
    Converts radian units from the Unwrapped Phase into absolute displacements
    using SNAP and copies the original phase/coherence bands into the new product.
    Args:
        product (org.esa.snap.core.datamodel.Product): SNAPHU Imported Sentinel-1 Product
    Returns:
        output (org.esa.snap.core.datamodel.Product): Phase to Displacement Sentinel-1 Product
    """
    parameters = HashMap()
    output = GPF.createProduct("PhaseToDisplacement", parameters, product)

    # Copying Coherence Band to the Displacement Product
    band_names = list(product.getBandNames())
    for band_name in band_names:
        if "coh" in band_name:
            coherence_band = band_name
        elif "Phase" in band_name:
            phase_band = band_name
    ProductUtils.copyBand(coherence_band, product, "coherence", output, True)
    ProductUtils.copyBand(phase_band, product, "phase", output, True)

    return output


def phase_to_elevation(product: object):
    """
    Converts radian units from the Unwrapped Phase into abosolute heights
    using SNAP and copies the original phase/coherence band into the new product.
    Args:
        product (org.esa.snap.core.datamodel.Product): SNAPHU Imported Sentinel-1 Product
    Returns:
        output (org.esa.snap.core.datamodel.Product): Phase to Elevation Sentinel-1 Product
    """
    parameters = HashMap()
    parameters.put("demName", "SRTM 1Sec HGT")
    output = GPF.createProduct("PhaseToElevation", parameters, product)

    # Copying Coherence Band to the Elevation Product
    band_names = list(product.getBandNames())
    for band_name in band_names:
        if "coh" in band_name:
            coherence_band = band_name
        elif "Phase" in band_name:
            phase_band = band_name

    ProductUtils.copyBand(coherence_band, product, "coherence", output, True)
    ProductUtils.copyBand(phase_band, product, "phase", output, True)

    return output


def terrain_correction(product: object, projection: str, savedem: bool = False):
    """
    Applies the Terrain Correction Operator within SNAP to correct SAR geometric distortions
    using a Digital Elevation model and produces a map projected output.
    Args:
        product (org.esa.snap.core.datamodel.Product): Phase to Displacement/Elevation Sentinel-1 Product
        savedem (bool): Set TRUE to write SRTM data used for Terrain Correction to a separate elevation band.
                        (Sentinel-1 DEM will be named `elevation_VV` and SRTM data is named `elevation`)
                        Defaults to False
    Returns:
        Terrain Corrected Sentinel-1 Product
    """
    parameters = HashMap()
    parameters.put("demName", "SRTM 1Sec HGT")
    parameters.put("mapProjection", projection)
    parameters.put("saveDEM", savedem)

    return GPF.createProduct("Terrain-Correction", parameters, product)


def coherence_mask(product: object, threshold: float) -> object:
    """
    Masks out Displacement image parts with low coherence by making them transparent using the
    Band Maths Operator within SNAP and saves the output as a new band.
    Args:
        product (org.esa.snap.core.datamodel.Product): Terrain Corrected Sentinel-1 Product
        threshold (float): Threshold for Coherence values to keep
    Returns:
        product (org.esa.snap.core.datamodel.Product): Coherence Masked Sentinel-1 Product
    """
    BandDescriptor = snappy.jpy.get_type(
        "org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor"
    )
    targetBand = BandDescriptor()
    targetBand.name = "displacement_VV_masked"
    targetBand.type = "float32"
    targetBand.expression = f"coherence_VV > {threshold}"

    targetBands = snappy.jpy.array(
        "org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor", 1
    )
    targetBands[0] = targetBand

    parameters = HashMap()
    parameters.put("targetBands", targetBands)
    masked_band = GPF.createProduct("BandMaths", parameters, product)

    ProductUtils.copyBand("displacement_VV_masked", masked_band, product, True)

    return product
