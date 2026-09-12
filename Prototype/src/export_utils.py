from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def json_bytes(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def save_csv_with_notice(df: pd.DataFrame, path: Path) -> None:
    out = df.copy()
    if "data_source" not in out.columns:
        out["data_source"] = "SIMULATED"
    out.to_csv(path, index=False)
