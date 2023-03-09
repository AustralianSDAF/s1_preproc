from pathlib import Path
import config as cfg
import subprocess
import utils as snap

# Main script to perform Displacement or Elevation INSAR Processing
# using SNAP 8 via SNAPPY Python API and GPT.
# User Configurable parameters can be found in config.py

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
filepath_1 = Path(cfg.filepath_1)
filepath_2 = Path(cfg.filepath_2)

# Setting up Intermediate Directories
work_dir.mkdir(exist_ok=True, parents=True)

temp_dir = Path(work_dir, "Temp")
temp_dir.mkdir(exist_ok=True, parents=True)

# Specifying Intermediate Output Paths
esd_image_path = Path(
    work_dir,
    f"{filepath_1.stem[:25]}_{filepath_2.stem[33:41]}_{cfg.processing}_split_Orb_Stack_esd.png",
)

pre_snaphu_path = Path(
    temp_dir,
    f"{filepath_1.stem[:25]}_{filepath_2.stem[33:41]}_{cfg.processing}_split_Orb_Stack_esd_ifg_deb_flt_ML.dim",
)

snaphu_export_path = Path(temp_dir, pre_snaphu_path.stem)

# Specifying Final Output Path
extensions = {"GeoTIFF": ".tif", "BEAM-DIMAP": ".dim"}
processed_product_path = Path(
    work_dir, f"{pre_snaphu_path.stem}_unw_phs_tc{extensions[cfg.write_file_format]}"
)

# =============================================================================
# Pre-SNAPHU Processing

# Loading both Sentinel-1 Products into SNAP
print("\nReading Images")
product_1, product_2 = snap.read_products(filepath_1=filepath_1, filepath_2=filepath_2)

# Checking the Perpendicular and Temporal Baselines of the Sentinel-1 Products
print("\nInSAR Overview")
perpendicular_baseline, temporal_baseline = snap.insar_stack_overview(
    product_1=product_1, product_2=product_2
)
print(f"Perpendicular Baseline: {perpendicular_baseline:.2f}m")
print(f"Temporal Baseline: {temporal_baseline:.2f} days")

# Ideally the Perpendicular Baseline should be greater than 150m and the Temporal Baseline should be between 6 - 12 days.
if perpendicular_baseline < 150 or temporal_baseline < 6 or temporal_baseline > 12:
    proceed = input(
        "Perpendicular and Temporal Baseline of the selected products are not optimal? Do you wish to proceed? (Y/N?)"
    )
    if proceed != "Y":
        print("Exiting")

# TOPSAR Split
# Ideally, we will add code to automatic select swaths and burst based on an AOI here
print("\nApplying TOPSAR Split Operation")
split_1 = snap.topsar_split(
    product=product_1,
    subswath=cfg.product_1_subswath,
    first_burst=cfg.product_1_first,
    last_burst=cfg.product_1_last,
)
split_2 = snap.topsar_split(
    product=product_2,
    subswath=cfg.product_2_subswath,
    first_burst=cfg.product_2_first,
    last_burst=cfg.product_2_last,
)

# Apply Orbit File
print("\nApplying Orbit Files")
orb_1 = snap.apply_orbit_file(product=split_1)
orb_2 = snap.apply_orbit_file(product=split_2)

# Coregistration - Back Geocoding
print("\nApplying Back-Geocoding Operation")
stack = snap.back_geocoding(product_1=orb_1, product_2=orb_2)

# Coregistration - Enhanced Spectral Diversity
print("\nApplying Enhanced Spectral Diversity Operation")
esd = snap.enhanced_spectral_diversity(product=stack)
print("Writing RGB Image")
snap.write_esd_rgb_image(product=esd, filename=esd_image_path)

# Interferogram
print("\nApplying Interferogram Operation")
subtract_topographic_phase = {"ELEVATION": False, "DISPLACEMENT": True}
ifg = snap.interferogram(
    product=esd, subtract_topographic_phase=subtract_topographic_phase[cfg.processing]
)

# TOPS Deburst
print("\nApplying TOPS Deburst Operation")
deb = snap.tops_deburst(product=ifg)

# Goldstein Phase Filtering
print("\nApplying Goldstein Phase Filtering Operation")
flt = snap.goldstein_phase_filtering(product=deb)

# Applying Multi-Looking
print("\nApplying Multi-Looking Operation")
ml = snap.multilooking(product=flt)

# Saving Intermediate Product
print("\nSaving Pre-SNAPHU Processed Product")
snap.write_product(product=ml, filepath=pre_snaphu_path, fileformat="BEAM-DIMAP")

# SNAPHU Export
print("\nPerforming SNAPHU Export Operation")
statcostmethod = {"ELEVATION": "TOPO", "DISPLACEMENT": "DEFO"}
snaphu_export = snap.snaphu_export_gpt(
    filepath=pre_snaphu_path,
    targetfolder=temp_dir,
    statcostmode=statcostmethod[cfg.processing],
    initmethod=cfg.init_method,
    numprocessors=cfg.num_processors,
)

# =============================================================================
# SNAPHU
print("\nPerforming Phase Unwrapping")
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
tc = snap.terrain_correction(product=phase, projection="WGS84(DD)", savedem=False)

# =============================================================================
# Saving Processed Product and Clean-up
print(f"\nSaving {cfg.processing} product as {cfg.write_file_format}!")
snap.write_product(
    product=tc, filepath=processed_product_path, fileformat=cfg.write_file_format
)

if cfg.del_intermediate_products is True:
    print("\nCleaning up Intermediate Files")
    subprocess.run(["rm", "-rf", str(temp_dir)], check=True)

print("Processing Complete!")
