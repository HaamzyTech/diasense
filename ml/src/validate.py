from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from config import ROOT
from utils.io import ensure_dirs, load_dataframe, parse_args, read_params, save_json, write_csv


def validate_dataframe(df: pd.DataFrame, EXPECTED_COLUMNS, RENAME_MAP, ZERO_AS_MISSING_COLS, valid_ranges) -> dict:
    report: dict = {
        "schema_ok": list(df.columns) == EXPECTED_COLUMNS,
        "expected_columns": EXPECTED_COLUMNS,
        "actual_columns": list(df.columns),
        "missing_values": df.isna().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "suspicious_ranges": {},
    }


    if not report["schema_ok"]:
        raise ValueError("Schema mismatch: expected exact columns and order")

    for column in EXPECTED_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df.rename(columns=RENAME_MAP, inplace=True)

    for col in ZERO_AS_MISSING_COLS:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            zero_mask = s.eq(0)
            df.loc[zero_mask, col] = np.nan

    
    ranges = {
        "pregnancies": (0, 30),
        "glucose": (0, 300),
        "blood_pressure": (0, 200),
        "skin_thickness": (0, 100),
        "insulin": (0, 1000),
        "bmi": (0, 100),
        "diabetes_pedigree_function": (0, 10),
        "age": (1, 120),
        "outcome": (0, 1),
    }

    for col, limits in valid_ranges.items():
        if col not in df.columns:
            continue

        s = pd.to_numeric(df[col], errors="coerce")
        lower = limits.get("min")
        upper = limits.get("max")

        invalid_mask = pd.Series(False, index=df.index)
        if lower is not None:
            invalid_mask = invalid_mask | (s < lower)
        if upper is not None:
            invalid_mask = invalid_mask | (s > upper)

        report["suspicious_ranges"][col] = int(invalid_mask.sum())

    report["row_count"] = int(len(df))
    report["null_rows"] = int(df.isna().any(axis=1).sum())
    report["is_valid"] = report["schema_ok"]
    return report

def add_optional_derived_features(df: pd.DataFrame, derived_cfg: dict[str, Any]) -> tuple[pd.DataFrame, list[str]]:
    created: list[str] = []
    
    if derived_cfg.get("bmi_group", True) and "bmi" in df.columns:
        bins = [-np.inf, 18.5, 25.0, 30.0, np.inf]
        labels = ["underweight", "normal", "overweight", "obese"]
        df["bmi_group"] = pd.cut(df["bmi"], bins=bins, labels=labels)
        created.append("bmi_group")

    if derived_cfg.get("age_band", True) and "age" in df.columns:
        bins = [-np.inf, 30.0, 45.0, 60.0, np.inf]
        labels = ["young", "adult", "middle_age", "older"]
        df["age_band"] = pd.cut(df["age"], bins=bins, labels=labels)
        created.append("age_band")

    return df, created


def main() -> None:
    args = parse_args()
    params = read_params(Path(ROOT / args.config))

    ensure_dirs(params)

    data_dir = params["paths"]["DATA_DIR"]
    raw_data = params["paths"]["raw_data"]
    dataset = params["files"]["dataset"]

    validated_dir = params["paths"]["validated_data"]
    
    validated_file = params["files"]["validated_dataset"]

    artifacts_dir = params["paths"]["ARTIFACTS_DIR"]
    reports_dir = params["paths"]["report_dir"]
    validation_report_file = params["files"]["validation_report"]

    EXPECTED_COLUMNS = params["schema"]["expected_cols"]
    RENAME_MAP = params["schema"]["rename_map"]
    ZERO_AS_MISSING_COLS = params["schema"]["zero_as_missing_columns"]
    derived_cfg = params["schema"]["derived_features"]

    valid_ranges = params["schema"]["valid_ranges"]

    input_path = ROOT / data_dir / raw_data / dataset
    output_path = ROOT / data_dir / validated_dir / validated_file
    report_path = ROOT / artifacts_dir / reports_dir / validation_report_file

    df = load_dataframe(input_path)

    

    report = validate_dataframe(df, EXPECTED_COLUMNS, RENAME_MAP, ZERO_AS_MISSING_COLS, valid_ranges)
    df, _ = add_optional_derived_features(df, derived_cfg)
    save_json(report_path, report)
    if not report["is_valid"]:
        raise ValueError("Validation failed; see validation_report.json")
    write_csv(output_path, df)


if __name__ == "__main__":
    main()
