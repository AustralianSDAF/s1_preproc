"""
Supplmentary script to pre-screen Sentinel-1 Products to check suitability for
InSAR Processing and automatically select Subswath and Burst Selection for S1 TOPS Split.

Author: Calvin Pang (calvin.pang@curtin.edu.au)
"""

from pathlib import Path
from config import work_dir, bounds
from src.processing_utils import read_products, insar_stack_overview, get_subswath_burst


def insar_precheck() -> None:
    """
    Screens Sentinel-1 products located the `data_raw` directory from the work_dir
    specified in the config file to produce a .csv report.
        1. Calculates the Perpendicular and Temporal Baselines for each chronological product pair using SNAPs InSAR Overview Operator
        2. Extracts the Subswath and Bursts covering an Area of Interest
    Args:
        None
    Returns:
        None
    """
    # Specifying the Raw Product Directory
    raw_dir = Path(work_dir, "data_raw")
    # Retrieving all .zip paths
    raw_paths = [(f, f.stem[17:25]) for f in Path(raw_dir).glob("*.zip")]

    # Sorting .zip paths by date
    if len(raw_paths) >= 2:
        raw_paths_sorted = sorted(raw_paths, key=lambda x: x[1])
    else:
        raise (ValueError("Insufficient Number of Files (Minimum of 2)"))

    # Preparing Pre-Check Results Header
    data = [
        "Product_1,Product_2,Perpendicular_Baseline,Temporal_Baseline,Baseline_Check,Product_1_Subswatch,Product_1_First_Burst,Product_1_Last_Burst,Product_2_Subswath,Product_2_First_Burst,Product_2_Last_Burst\n"
    ]

    # Processing Files
    for path_1, path_2 in zip(raw_paths_sorted, raw_paths_sorted[1:]):
        # InSAR Overview
        read_1, read_2 = read_products(path_1[0], path_2[0])
        perpendicular_baseline, temporal_baseline = insar_stack_overview(read_1, read_2)

        # Optimal Results
        # Perpendicular Baseline: 150 - 300m
        # Temporal Baseline: 6 - 12 days
        if (
            abs(perpendicular_baseline) < 150
            or temporal_baseline < 6
            or temporal_baseline > 12
        ):
            baseline_result = "FAIL"
        else:
            baseline_result = "PASS"

        subswaths_dict = get_subswath_burst(
            filepath_1=path_1[0], filepath_2=path_2[0], aoi=bounds
        )

        # Writing the Results
        for subswath, bursts in subswaths_dict.items():
            product_1_first = bursts["product_1"][0]
            product_1_last = bursts["product_1"][1]
            product_2_first = bursts["product_2"][0]
            product_2_last = bursts["product_2"][1]

            data.append(
                f"{path_1[0].name},{path_2[0].name},{perpendicular_baseline},{temporal_baseline},{baseline_result},{subswath},{product_1_first},{product_1_last},{subswath},{product_2_first},{product_2_last}\n"
            )

    with open(
        file=Path(work_dir, "precheck_output.csv"), mode="w", encoding="UTF-8"
    ) as f:
        f.writelines(data)

if __name__ == "__main__":
    insar_precheck()
