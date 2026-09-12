from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_prominences


def _signal_features(freq: np.ndarray, values: np.ndarray, prefix: str) -> dict[str, float]:
    max_i, min_i = int(np.argmax(values)), int(np.argmin(values))
    prominences: list[float] = []
    for signal in (values, -values):
        peaks, _ = find_peaks(signal)
        if peaks.size:
            prominences.extend(peak_prominences(signal, peaks)[0].tolist())
    return {
        f"{prefix}_max_db": float(values[max_i]),
        f"{prefix}_min_db": float(values[min_i]),
        f"{prefix}_mean_db": float(np.mean(values)),
        f"{prefix}_median_db": float(np.median(values)),
        f"{prefix}_std_db": float(np.std(values, ddof=0)),
        f"{prefix}_range_db": float(np.ptp(values)),
        f"{prefix}_slope": float(np.polyfit(freq, values, 1)[0]),
        f"{prefix}_auc": float(np.trapezoid(values, freq)),
        f"{prefix}_max_frequency_ghz": float(freq[max_i]),
        f"{prefix}_min_frequency_ghz": float(freq[min_i]),
        f"{prefix}_strongest_prominence_db": float(max(prominences, default=0.0)),
    }


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for measurement_id, group in df.groupby("measurement_id", sort=True):
        group = group.sort_values("frequency_ghz")
        freq = group["frequency_ghz"].to_numpy(float)
        first = group.iloc[0]
        record = {
            "sample_id": first["sample_id"], "measurement_id": measurement_id,
            "label": first["label"], "data_source": first["data_source"],
        }
        record.update(_signal_features(freq, group["s11_db"].to_numpy(float), "s11"))
        record.update(_signal_features(freq, group["s21_db"].to_numpy(float), "s21"))
        records.append(record)
    return pd.DataFrame(records)
