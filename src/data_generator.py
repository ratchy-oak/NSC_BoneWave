"""Deterministic signals for software testing, not biological/EM simulation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import FREQUENCY_MAX_GHZ, FREQUENCY_MIN_GHZ, FREQUENCY_POINTS, LABELS, SEED


def _lorentzian(x: np.ndarray, center: float, width: float) -> np.ndarray:
    return 1.0 / (1.0 + ((x - center) / width) ** 2)


def generate_synthetic_data(
    samples_per_class: int = 10,
    measurements_per_sample: int = 3,
    seed: int = SEED,
) -> pd.DataFrame:
    if samples_per_class < 1 or measurements_per_sample < 1:
        raise ValueError("จำนวนตัวอย่างและจำนวนการวัดซ้ำต้องมากกว่าศูนย์")
    rng = np.random.default_rng(seed)
    freq = np.linspace(FREQUENCY_MIN_GHZ, FREQUENCY_MAX_GHZ, FREQUENCY_POINTS)
    rows: list[pd.DataFrame] = []
    # Differences are intentionally modest and noisy so classes overlap.
    effects = {
        "Normal": (0.000, 0.00, 0.00),
        "Crack Risk": (0.025, 0.55, 0.40),
        "High Fracture Risk": (0.050, 1.00, 0.75),
    }
    for class_index, label in enumerate(LABELS):
        shift, s11_effect, s21_effect = effects[label]
        for sample_index in range(samples_per_class):
            sample_id = f"C{class_index + 1:02d}-S{sample_index + 1:03d}"
            sample_shift = shift + rng.normal(0, 0.028)
            sample_gain = rng.normal(0, 0.65)
            sample_phase = rng.uniform(0, 2 * np.pi)
            width = np.clip(0.105 + rng.normal(0, 0.015), 0.065, 0.16)
            for repeat in range(measurements_per_sample):
                measurement_id = f"{sample_id}-M{repeat + 1:02d}"
                repeat_shift = sample_shift + rng.normal(0, 0.006)
                resonance = _lorentzian(freq, 2.18 + repeat_shift, width)
                secondary = _lorentzian(freq, 2.62 + repeat_shift * 0.45, 0.10)
                ripple = np.sin(2 * np.pi * 2.1 * (freq - 1.5) + sample_phase)
                s11 = (-10.8 + 0.55 * (freq - 2.25) - (4.5 + s11_effect) * resonance
                       - 1.15 * secondary + 0.30 * ripple + sample_gain
                       + rng.normal(0, 0.30, freq.size))
                s21 = (-3.5 - 1.15 * (freq - 1.5) - (2.2 + s21_effect) * resonance
                       - 0.45 * secondary + 0.18 * ripple - sample_gain * 0.24
                       + rng.normal(0, 0.24, freq.size))
                rows.append(pd.DataFrame({
                    "frequency_ghz": freq, "s11_db": s11, "s21_db": s21,
                    "sample_id": sample_id, "measurement_id": measurement_id,
                    "label": label, "data_source": "SIMULATED",
                }))
    return pd.concat(rows, ignore_index=True)
