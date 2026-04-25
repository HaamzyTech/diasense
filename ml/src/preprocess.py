from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from config import ROOT
from utils.io import ensure_dirs, parse_args, read_params, save_json, write_csv


def preprocess_dataframe(df: pd.DataFrame, IMPUTE_ZERO_AS_MISSING, FEATURE_COLUMNS) -> tuple[pd.DataFrame, dict]:
    processed = df.copy()
    for column in IMPUTE_ZERO_AS_MISSING:
        processed[column] = processed[column].replace(0, pd.NA)

    medians = {}
    for column in FEATURE_COLUMNS:
        processed[column] = pd.to_numeric(processed[column], errors="coerce")
        medians[column] = float(processed[column].median())
        processed[column] = processed[column].fillna(medians[column])

    processed["outcome"] = pd.to_numeric(processed["outcome"], errors="raise").astype(int)
    return processed, {"medians": medians}

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

def stratified_split(
    df: pd.DataFrame,
    target_column: str,
    random_state: int,
    train_size: float,
    val_size: float,
    test_size: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    total = train_size + val_size + test_size
    if not np.isclose(total, 1.0):
        raise ValueError("train_size + val_size + test_size must equal 1.0")

    train_df, temp_df = train_test_split(
        df,
        test_size=(1.0 - train_size),
        stratify=df[target_column],
        random_state=random_state,
    )

    temp_fraction_for_test = test_size / (val_size + test_size)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=temp_fraction_for_test,
        stratify=temp_df[target_column],
        random_state=random_state,
    )

    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def compute_fill_values(train_df: pd.DataFrame, numeric_cols: list[str], categorical_cols: list[str]) -> dict[str, Any]:
    fill_values: dict[str, Any] = {}
    for col in numeric_cols:
        value = pd.to_numeric(train_df[col], errors="coerce").median()
        fill_values[col] = None if pd.isna(value) else float(value)
    for col in categorical_cols:
        mode = train_df[col].astype("string").mode(dropna=True)
        fill_values[col] = "missing" if len(mode) == 0 else str(mode.iloc[0])
    return fill_values


def apply_fill_values(df: pd.DataFrame, fill_values: dict[str, Any], numeric_cols: list[str], categorical_cols: list[str]) -> pd.DataFrame:
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(fill_values[col])
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype("string").fillna(fill_values[col])
    return df

def apply_clip_bounds(df: pd.DataFrame, bounds: dict[str, dict[str, float]]) -> tuple[pd.DataFrame, dict[str, int]]:
    clipped_counts: dict[str, int] = {}
    for col, limit in bounds.items():
        if col not in df.columns:
            continue
        before = pd.to_numeric(df[col], errors="coerce")
        after = before.clip(lower=limit["lower"], upper=limit["upper"])
        changed = int(((before != after) & ~(before.isna() & after.isna())).sum())
        df[col] = after
        clipped_counts[col] = changed
    return df, clipped_counts

def compute_clip_bounds(train_df: pd.DataFrame, numeric_cols: list[str], outlier_cfg: dict[str, Any]) -> dict[str, dict[str, float]]:
    if not outlier_cfg.get("enabled", True):
        return {}

    method = str(outlier_cfg.get("method", "iqr")).lower()
    bounds: dict[str, dict[str, float]] = {}

    if method == "iqr":
        multiplier = float(outlier_cfg.get("multiplier", 1.5))
        for col in numeric_cols:
            s = pd.to_numeric(train_df[col], errors="coerce")
            q1 = float(s.quantile(0.25))
            q3 = float(s.quantile(0.75))
            iqr = q3 - q1
            bounds[col] = {
                "lower": q1 - multiplier * iqr,
                "upper": q3 + multiplier * iqr,
            }
    elif method == "quantile":
        lower_q = float(outlier_cfg.get("lower_quantile", 0.01))
        upper_q = float(outlier_cfg.get("upper_quantile", 0.99))
        for col in numeric_cols:
            s = pd.to_numeric(train_df[col], errors="coerce")
            bounds[col] = {
                "lower": float(s.quantile(lower_q)),
                "upper": float(s.quantile(upper_q)),
            }
    else:
        raise ValueError("preprocess.outlier.method must be 'iqr' or 'quantile'.")

    return bounds
def main() -> None:
    args = parse_args()
    params = read_params(Path(ROOT / args.config))

    ensure_dirs(params)

    data_dir = params["paths"]["DATA_DIR"] 
    validated_dir = params["paths"]["validated_data"]
    processed_dir = params["paths"]["processed_data"]
    features_dir = params["paths"]["feature_data"]
    
    validated_file = params["files"]["validated_dataset"]
    snapshot_file = params["files"]["raw_snapshot"]
    processed_file = params["files"]["processed_dataset"]

    artifacts_dir = params["paths"]["ARTIFACTS_DIR"]
    reports_dir = params["paths"]["report_dir"]
    train_data = params["files"]["train_set"]
    test_data = params["files"]["test_set"]
    val_data = params["files"]["val_set"]
    prep_artifact_file = params["files"]["preprocessing_artifact"]

    ZERO_AS_MISSING_COLS = params["schema"]["zero_as_missing_columns"]
    FEATURE_COLS = params["schema"]["feature_cols"]
    derived_cfg = params["schema"]["derived_features"]

    target_column = params["data"]["target_column"]

    train_size = params["data"]["train_size"]
    val_size = params["data"]["val_size"]
    test_size = params["data"]["test_size"]
    random_state = params["data"]["random_state"]

    preprocess_config = params["preprocess"]

    validated_path = ROOT / data_dir / validated_dir / validated_file
    raw_snapshot_path = ROOT / data_dir / processed_dir / snapshot_file

    df = pd.read_csv(validated_path)
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in validated dataset.")

    write_csv(raw_snapshot_path, df)

    df, _ = add_optional_derived_features(df, derived_cfg)
    processed, artifact = preprocess_dataframe(df, ZERO_AS_MISSING_COLS, FEATURE_COLS)
    try:
        train_df, val_df, test_df = stratified_split(
            df=processed,
            target_column=target_column,
            random_state=random_state,
            train_size=train_size,
            val_size=val_size,
            test_size=test_size,
        )
    except ValueError as e:
        raise ValueError(
            "Stratified split failed. One or more classes are too rare for 70/15/15."
        ) from e
    
    numeric_cols = [
        c for c in train_df.columns
        if c != target_column and pd.api.types.is_numeric_dtype(train_df[c])
    ]
    categorical_cols = [
        c for c in train_df.columns
        if c != target_column and not pd.api.types.is_numeric_dtype(train_df[c])
    ]

    fill_values = compute_fill_values(train_df, numeric_cols, categorical_cols)
    train_fit_df = apply_fill_values(train_df.copy(), fill_values, numeric_cols, categorical_cols)
    val_fit_df = apply_fill_values(val_df.copy(), fill_values, numeric_cols, categorical_cols)
    test_fit_df = apply_fill_values(test_df.copy(), fill_values, numeric_cols, categorical_cols)

    outlier_cfg = preprocess_config.get("outlier", {})
    clip_columns = list(outlier_cfg.get("columns", numeric_cols))
    clip_columns = [c for c in clip_columns if c in numeric_cols]
    clip_bounds = compute_clip_bounds(train_fit_df, clip_columns, outlier_cfg)

    train_fit_df, train_clip_report = apply_clip_bounds(train_fit_df, clip_bounds)
    val_fit_df, val_clip_report = apply_clip_bounds(val_fit_df, clip_bounds)
    test_fit_df, test_clip_report = apply_clip_bounds(test_fit_df, clip_bounds)

    artifact["train_clip_report"] = train_clip_report
    artifact["val_clip_report"] = val_clip_report
    artifact["test_clip_report"] = test_clip_report

    cleaned_df = pd.concat([train_fit_df, val_fit_df,test_fit_df])

    write_csv(ROOT / data_dir / processed_dir / processed_file, cleaned_df)
    write_csv(ROOT / data_dir / features_dir/ train_data, train_fit_df)
    write_csv(ROOT / data_dir / features_dir/ val_data, val_fit_df)
    write_csv(ROOT / data_dir / features_dir/ test_data, test_fit_df)
    preprocessing_artifact_path = ROOT / artifacts_dir / reports_dir / prep_artifact_file
    save_json(preprocessing_artifact_path, artifact)


if __name__ == "__main__":
    main()
