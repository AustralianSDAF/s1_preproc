"""
Script to perform Displacement or Elevation INSAR Processing using SNAP 8 via SNAPPY Python API and GPT.
User Configurable parameters can be found in config.py

Author: Calvin Pang (calvin.pang@curtin.edu.au)
"""

from pathlib import Path
import subprocess
import sys

import config as cfg
import src.processing_utils as snap


def insar_processing(
    filename_1: Path = cfg.filename_1, filename_2: Path = cfg.filename_2
):
    """
    Function containing the Displacement and Elevation pipelines.
    Args:
        filename_1 (Path): Filename for first Sentinel-1 Product (Older)
        filename_2 (Path): Filename for second Sentinel-1 Product (Newer)
    Returns:
        None
    """

    # =============================================================================
    # Config Input Validation
    allowed_values = ["GeoTIFF", "BEAM-DIMAP", "ELEVATION", "DISPLACEMENT"]
    if cfg.write_file_format not in allowed_values:
        raise ValueError(
            f"Invalid Write Format: {cfg.write_file_format}. Allowed Values: BEAM-DIMAP, GeoTIFF"
        )
    if cfg.processing not in allowed_values:
        raise ValueError(
            f"Invalid INSAR Processing: {cfg.processing}. Allowed Values: DISPLACEMENT or ELEVATION"
        )

    # =============================================================================
    # Specifying up Input Filepaths
    work_dir = Path(cfg.work_dir)
    filepath_1 = Path(work_dir, "data_raw", filename_1)
    filepath_2 = Path(work_dir, "data_raw", filename_2)

    # Setting up Intermediate Directories
    work_dir.mkdir(exist_ok=True, parents=True)

    temp_dir = Path(work_dir, "Temp")
    temp_dir.mkdir(exist_ok=True, parents=True)

    # =============================================================================
    # Pre-SNAPHU Processing

    # Loading both Sentinel-1 Products into SNAP
    print("\nReading Images")
    product_1, product_2 = snap.read_products(
        filepath_1=filepath_1, filepath_2=filepath_2
    )

    # # Checking the Perpendicular and Temporal Baselines of the Sentinel-1 Products
    # print("\nInSAR Overview")
    # perpendicular_baseline, temporal_baseline = snap.insar_stack_overview(
    #     product_1=product_1, product_2=product_2
    # )
    # print(f"Perpendicular Baseline: {perpendicular_baseline:.2f}m")
    # print(f"Temporal Baseline: {temporal_baseline:.2f} days")

    # # Ideally the Perpendicular Baseline should be greater than 150m and the Temporal Baseline should be between 6 - 12 days.
    # if abs(perpendicular_baseline) < 150 or temporal_baseline < 6 or temporal_baseline > 12:
    #     proceed = input(
    #         "Perpendicular and Temporal Baseline of the selected products are not optimal? Do you wish to proceed? (Y/N?)"
    #     )
    #     if proceed != "Y":
    #         raise ValueError(f'Invalid Input - {proceed}. Exiting')

    # Retrieving TOPSAR Split Parameters
    topsar_params = snap.get_subswath_burst(
        filepath_1=filepath_1, filepath_2=filepath_2, aoi=cfg.bounds
    )

    # Processing each Subswath Separately
    for subswath, bursts in topsar_params.items():
        # =============================================================================
        # Checking if already processed and skipping if already complete
        matching_files = list(
            work_dir.glob(
                f"*{filepath_1.stem[:25]}_{filepath_2.stem[33:41]}_{cfg.processing}_{subswath}*.dim"
            )
        ) + list(
            work_dir.glob(
                f"*{filepath_1.stem[:25]}_{filepath_2.stem[33:41]}_{cfg.processing}_{subswath}*.tif"
            )
        )
        if len(matching_files) <= 0:
            # TOPSAR Split
            print("\nApplying TOPSAR Split Operation")
            product_1_first = bursts["product_1"][0]
            product_1_last = bursts["product_1"][1]
            split_1 = snap.topsar_split(
                product=product_1,
                subswath=subswath,
                first_burst=product_1_first,
                last_burst=product_1_last,
            )
            product_2_first = bursts["product_2"][0]
            product_2_last = bursts["product_2"][1]

            split_2 = snap.topsar_split(
                product=product_2,
                subswath=subswath,
                first_burst=product_2_first,
                last_burst=product_2_last,
            )

            # Apply Orbit File
            print("\nApplying Orbit Files")
            orb_1 = snap.apply_orbit_file(product=split_1)
            orb_2 = snap.apply_orbit_file(product=split_2)

            # Coregistration - Back Geocoding
            print("\nApplying Back-Geocoding Operation")
            stack = snap.back_geocoding(product_1=orb_1, product_2=orb_2)

            # Coregistration - Enhanced Spectral Diversity
            # Only required if more than one burst is selected
            # Check whether Enhanced Spectral Diversity is Required
            if (product_1_last - product_1_first) > 0 or (
                product_2_last - product_2_first
            ) > 0:
                apply_esd = True
                esd_str = "_esd"
            else:
                apply_esd = False
                esd_str = ""

            if apply_esd:
                print("\nApplying Enhanced Spectral Diversity Operation")
                esd = snap.enhanced_spectral_diversity(product=stack)
            else:
                esd = stack
            
            if cfg.write_rgb is True:
                print("Writing RGB Image")
                rgb_image_path = Path(
                    work_dir,
                    f"{filepath_1.stem[:25]}_{filepath_2.stem[33:41]}_{cfg.processing}_{subswath}_split_Orb_Stack{esd_str}.png",
                )
                snap.write_rgb_image(product=esd, filename=rgb_image_path)

            # Interferogram
            print("\nApplying Interferogram Operation")
            subtract_topographic_phase = {"ELEVATION": False, "DISPLACEMENT": True}
            ifg = snap.interferogram(
                product=esd,
                subtract_topographic_phase=subtract_topographic_phase[cfg.processing],
            )

            # TOPS Deburst
            print("\nApplying TOPS Deburst Operation")
            deb = snap.tops_deburst(product=ifg)

            # Goldstein Phase Filtering
            print("\nApplying Goldstein Phase Filtering Operation")
            flt = snap.goldstein_phase_filtering(product=deb)

            # Apply Subset
            if cfg.subset is True:
                print("\nApplying Subset Operation")
                flt = snap.subset(product=flt, aoi=cfg.bounds)

            # Applying Multi-Looking
            print("\nApplying Multi-Looking Operation")
            ml = snap.multilooking(product=flt)

            # Saving Intermediate Product
            print("\nSaving Pre-SNAPHU Processed Product")
            pre_snaphu_path = Path(
                temp_dir,
                f"{filepath_1.stem[:25]}_{filepath_2.stem[33:41]}_{cfg.processing}_{subswath}_split_Orb_Stack{esd_str}_ifg_deb_flt_ML.dim",
            )
            snap.write_product(
                product=ml, filepath=pre_snaphu_path, fileformat="BEAM-DIMAP"
            )

            # SNAPHU Export
            print("\nPerforming SNAPHU Export Operation")
            statcostmethod = {"ELEVATION": "TOPO", "DISPLACEMENT": "DEFO"}
            snaphu_export = snap.snaphu_export_gpt(
                filepath=pre_snaphu_path,
                targetfolder=temp_dir,
                statcostmode=statcostmethod[cfg.processing],
                initmethod=cfg.init_method,
                numprocessors=cfg.num_processors,
                rowoverlap=cfg.row_overlap,
                coloverlap=cfg.col_overlap,
            )

            # =============================================================================
            # SNAPHU
            print("\nPerforming Phase Unwrapping")
            snaphu_export_path = Path(temp_dir, pre_snaphu_path.stem)
            unw = snap.snaphu_unwrapping(filepath=snaphu_export_path)

            # =============================================================================
            # Post-SNAPHU Processing
            print("\nPerforming SNAPHU Import Operation")
            snaphu_import = snap.snaphu_import(
                preprocessed_product=ml, snaphu_export_path=snaphu_export_path
            )

            # Phase to Displacement/Elevation
            if cfg.processing == "ELEVATION":
                print("\nApplying Phase to Elevation Operation")
                phase = snap.phase_to_elevation(product=snaphu_import)
            else:
                print("\nApplying Phase to Displacement Operation")
                phase = snap.phase_to_displacement(product=snaphu_import)

            # Terrain Correction
            print("\nApplying Terrain Correction Operation")
            tc = snap.terrain_correction(
                product=phase, projection="WGS84(DD)", savedem=False
            )

            # =============================================================================
            # Saving Processed Product and Clean-up
            print(f"\nSaving {cfg.processing} product as {cfg.write_file_format}!")
            extensions = {"GeoTIFF": ".tif", "BEAM-DIMAP": ".dim"}
            processed_product_path = Path(
                work_dir,
                f"{pre_snaphu_path.stem}_unw_phs_tc{extensions[cfg.write_file_format]}",
            )
            snap.write_product(
                product=tc,
                filepath=processed_product_path,
                fileformat=cfg.write_file_format,
            )

            if cfg.del_intermediate_products is True:
                print("\nCleaning up Intermediate Files")
                subprocess.run(["rm", "-rf", str(temp_dir)], check=True)
            print("Processing Complete!")
        else:
            print(f"{matching_files[0]} already exists - Skipping")
    # Clears JVM Memory Cache after Processing Product Pair
    snap.garbage_collection()


if __name__ == "__main__":
    # Required for batch processing...
    if len(sys.argv) > 1:
        input_1 = sys.argv[1]
        input_2 = sys.argv[2]
        insar_processing(filename_1=input_1, filename_2=input_2)
    else:
        insar_processing()
