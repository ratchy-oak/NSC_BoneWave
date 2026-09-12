from __future__ import annotations

from io import BytesIO
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay

from .constants import LABELS


def figure_to_png(fig) -> bytes:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    return buffer.getvalue()


def plot_measurement(df: pd.DataFrame, measurement_id: str):
    selected = df[df["measurement_id"] == measurement_id].sort_values("frequency_ghz")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharex=True)
    for ax, col, title in zip(axes, ["s11_db", "s21_db"], ["S11", "S21"]):
        ax.plot(selected["frequency_ghz"], selected[col], lw=1.6, label=f"{title} (simulated)")
        ax.set(title=f"{title} — Simulated measurement", xlabel="Frequency (GHz)", ylabel=f"{title} (dB)")
        ax.grid(alpha=.25); ax.legend()
    fig.suptitle(f"BoneWave synthetic signal: {measurement_id}")
    fig.tight_layout()
    return fig


def plot_average_by_class(df: pd.DataFrame):
    avg = df.groupby(["label", "frequency_ghz"])[["s11_db", "s21_db"]].mean().reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for label in LABELS:
        part = avg[avg["label"] == label]
        axes[0].plot(part.frequency_ghz, part.s11_db, label=label)
        axes[1].plot(part.frequency_ghz, part.s21_db, label=label)
    for ax, name in zip(axes, ["S11", "S21"]):
        ax.set(title=f"Average {name} by synthetic class", xlabel="Frequency (GHz)", ylabel=f"{name} (dB)")
        ax.grid(alpha=.25); ax.legend(fontsize=8)
    fig.tight_layout(); return fig


def plot_metric_comparison(metrics: pd.DataFrame):
    cols = ["accuracy", "macro_precision", "macro_recall", "macro_f1"]
    ax = metrics.set_index("model")[cols].plot.bar(figsize=(9, 4), ylim=(0, 1), rot=0)
    ax.set(title="Model comparison — synthetic data only", xlabel="Model", ylabel="Score")
    ax.legend(ncol=4, fontsize=8); ax.grid(axis="y", alpha=.25)
    return ax.figure


def plot_class_distribution(features: pd.DataFrame):
    counts = features.groupby("label")["sample_id"].nunique().reindex(LABELS)
    ax = counts.plot.bar(figsize=(7, 4), color="#4776a8", rot=15)
    ax.set(title="Unique simulated samples by class", xlabel="Synthetic class", ylabel="Number of samples")
    ax.grid(axis="y", alpha=.25); return ax.figure


def save_confusion_matrix(cm: np.ndarray, model_name: str, path: Path):
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(cm, display_labels=LABELS).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(f"{model_name} confusion matrix — simulated data")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout(); fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)


def save_feature_importance(model, feature_names: list[str], model_name: str, path: Path) -> bool:
    if not hasattr(model, "feature_importances_"):
        return False
    order = np.argsort(model.feature_importances_)[-12:]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(np.array(feature_names)[order], model.feature_importances_[order])
    ax.set(title=f"{model_name} feature importance — synthetic data", xlabel="Importance")
    fig.tight_layout(); fig.savefig(path, dpi=180, bbox_inches="tight"); plt.close(fig)
    return True
