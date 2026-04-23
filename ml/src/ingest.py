import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from config import ROOT
from utils.io import ensure_dirs, load_dataframe, parse_args, read_params, save_json

def infer_schema(df:pd.DataFrame) -> list[dict[str, Any]]:
    schema: list[dict[str, Any]] = []

    for column in df.columns:
        series = df[column]
        schema.append({
            "name": str(column),
            "dtype": str(series.dtype),
            "nullable": bool(series.isna().any()),
            "null_count": int(series.isna().sum()),
        })
    return schema
def build_metrics(df: pd.DataFrame, raw_file_path: Path, schema_fingerprint: str) -> dict[str, Any]:
    return {
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "duplicate_row_count": int(df.duplicated().sum()),
        "file_size_bytes": int(raw_file_path.stat().st_size),
        "schema_hash": schema_fingerprint,
    }

def schema_hash(schema: list[dict[str, Any]]) -> str:
    encoded = json.dumps(schema, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def main() -> None:
    print("Starting data ingestion...")
    args = parse_args()
    params = read_params(Path(ROOT / args.config))

    ensure_dirs(params)

    source_url = params["data"]["source_url"]
    data_dir = params["paths"]["DATA_DIR"]
    artifacts_dir = params["paths"]["ARTIFACTS_DIR"]
    raw_data = params["paths"]["raw_data"]
    dataset = params["files"]["dataset"]
    request_timeout = params["data"]["time_out"]

    output = ROOT / data_dir / raw_data / dataset

    with requests.get(source_url, stream=True, timeout=request_timeout) as response:
        response.raise_for_status()
        with open(output, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    output_file.write(chunk)

    df = load_dataframe(output)
    schema = infer_schema(df)
    schema_fingerprint = schema_hash(schema)
    metrics = build_metrics(df, output, schema_fingerprint)

    reports_dir = params["paths"]["report_dir"]
    schema_file = params["files"]["schema"]
    metrics_file = params["files"]["metrics"]

    schema_path = ROOT / artifacts_dir / reports_dir / schema_file
    metrics_path = ROOT / artifacts_dir / reports_dir / metrics_file

    save_json(schema_path, {"columns": schema, "schema_hash": schema_fingerprint})
    save_json(metrics_path, metrics)

    print(f"[OK] Raw dataset saved to: {output}")
    print(f"[OK] Schema written to: {schema_path}")
    print(f"[OK] Metrics written to: {metrics_path}")

    print("Data ingestion completed successfully!")

if __name__ == "__main__":
    main()
