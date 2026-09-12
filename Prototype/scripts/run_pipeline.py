#!/usr/bin/env python3
"""Run the complete BoneWave non-UI synthetic demonstration pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
from src.constants import FEATURE_DIR, FIGURE_DIR, PROCESSED_DIR, RAW_DIR, ensure_directories
from src.data_generator import generate_synthetic_data
from src.data_validation import validate_dataframe
from src.feature_extraction import extract_features
from src.modeling import train_and_evaluate
from src.preprocessing import preprocess_data
from src.visualization import plot_average_by_class, plot_class_distribution, plot_measurement, plot_metric_comparison


def run_pipeline() -> dict:
    ensure_directories()
    raw = generate_synthetic_data()
    validation = validate_dataframe(raw)
    if not validation.valid:
        raise RuntimeError("Generated data failed validation: " + "; ".join(validation.errors))
    raw.to_csv(RAW_DIR / "simulated_sparameters.csv", index=False)
    processed, _ = preprocess_data(raw, interpolate=False, smooth=False)
    processed.to_csv(PROCESSED_DIR / "simulated_sparameters_processed.csv", index=False)
    features = extract_features(processed)
    features.to_csv(FEATURE_DIR / "simulated_features.csv", index=False)
    result = train_and_evaluate(features)
    figures = {
        "example_s11_s21.png": plot_measurement(raw, raw.measurement_id.iloc[0]),
        "average_signals_by_class.png": plot_average_by_class(raw),
        "class_distribution.png": plot_class_distribution(features),
        "model_metric_comparison.png": plot_metric_comparison(result["metrics"]),
    }
    for filename, fig in figures.items():
        fig.savefig(FIGURE_DIR / filename, dpi=180, bbox_inches="tight")
        plt.close(fig)
    print("BoneWave synthetic pipeline completed successfully.")
    print(result["metrics"].to_string(index=False))
    print("WARNING: These are simulated software-demo metrics, not medical performance.")
    return result


if __name__ == "__main__":
    run_pipeline()
