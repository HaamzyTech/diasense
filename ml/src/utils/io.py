import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from config import ROOT

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read params")
    parser.add_argument("--config", default="params.yaml", help="Path to params.yaml")
    return parser.parse_args()

def ensure_dirs( params: dict[str, Any] ) -> None:
    params = params["paths"]
    DATA_DIR = Path(ROOT / params["DATA_DIR"])
    ARTIFACTS_DIR = Path(ROOT / params["ARTIFACTS_DIR"])

    (DATA_DIR / params["raw_data"]).mkdir(parents=True, exist_ok=True)
    (DATA_DIR / params["validated_data"]).mkdir(parents=True, exist_ok=True)
    (DATA_DIR / params["processed_data"]).mkdir(parents=True, exist_ok=True)
    (DATA_DIR / params["feature_data"]).mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / params["report_dir"]).mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / params["model_dir"]).mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / params["baseline_dir"]).mkdir(parents=True, exist_ok=True)


def read_params(path: Path) -> dict[str, Any]:
    import yaml

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_csv(path: Path, data: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False)


def save_model(path: Path, model: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: Path) -> Any:
    return joblib.load(path)

def load_dataframe(path: Path) -> pd.DataFrame:
    suffix = Path(path).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    
    raise ValueError(
        f"Unsupported file format: {suffix}. "
        "Use .csv, .parquet, .xlsx, or .xls files"
    )