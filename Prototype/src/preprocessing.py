from __future__ import annotations

import pandas as pd
from scipy.signal import savgol_filter


def preprocess_data(
    df: pd.DataFrame,
    interpolate: bool = False,
    smooth: bool = False,
    window_length: int = 11,
    polyorder: int = 2,
) -> tuple[pd.DataFrame, list[str]]:
    out = df.copy(deep=True).sort_values(["measurement_id", "frequency_ghz"]).reset_index(drop=True)
    operations = ["เรียงข้อมูลตาม measurement_id และ frequency_ghz"]
    if interpolate:
        out[["s11_db", "s21_db"]] = out.groupby("measurement_id")[["s11_db", "s21_db"]].transform(
            lambda x: x.interpolate(limit=3, limit_direction="both")
        )
        operations.append("interpolate ช่องว่างขนาดเล็ก (ไม่เกิน 3 จุด)")
    if out[["s11_db", "s21_db"]].isna().any().any():
        raise ValueError("ยังมีค่าว่างหลังการเตรียมข้อมูล")
    grouped_grids = [group["frequency_ghz"].to_numpy() for _, group in out.groupby("measurement_id", sort=False)]
    grid_counts = out.groupby("measurement_id")["frequency_ghz"].nunique()
    if grid_counts.nunique() != 1:
        raise ValueError("จำนวนจุดใน frequency grid ของแต่ละ measurement ไม่ตรงกัน")
    reference = grouped_grids[0]
    if any(len(grid) != len(reference) or not (abs(grid - reference) < 1e-9).all() for grid in grouped_grids[1:]):
        raise ValueError("frequency grid ของแต่ละ measurement ไม่ตรงกัน; กรุณาจัดแนว grid ก่อน")
    if smooth:
        if window_length % 2 == 0 or window_length <= polyorder:
            raise ValueError("Savitzky–Golay window ต้องเป็นเลขคี่และมากกว่า polyorder")
        for col in ("s11_db", "s21_db"):
            out[col] = out.groupby("measurement_id")[col].transform(
                lambda x: savgol_filter(x.to_numpy(), window_length, polyorder) if len(x) >= window_length else x
            )
        operations.append(f"Savitzky–Golay smoothing (window={window_length}, polyorder={polyorder})")
    else:
        operations.append("ไม่ได้ใช้ smoothing")
    out["preprocessing_operations"] = "; ".join(operations)
    return out, operations
