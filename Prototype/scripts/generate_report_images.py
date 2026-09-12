#!/usr/bin/env python3
"""Create factual report images from the implemented BoneWave project."""
from __future__ import annotations

import subprocess
import sys
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
sys.path.insert(0, str(ROOT))
plt.rcParams["font.family"] = "DejaVu Sans"


def evidence_canvas(title: str, subtitle: str = "SIMULATED DATA • Research proof-of-concept • Not a medical device"):
    fig, ax = plt.subplots(figsize=(14, 8), facecolor="#f7fafb")
    ax.set_facecolor("#f7fafb"); ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis("off")
    ax.text(.65, 7.45, title, fontsize=21, fontweight="bold", color="#173b47", va="top")
    ax.text(.65, 7.02, subtitle, fontsize=10.5, color="#9b4d16", va="top")
    return fig, ax


def save_evidence(fig, filename):
    fig.savefig(OUT / filename, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def overview_image():
    metrics = pd.read_csv(ROOT / "results" / "model_metrics.csv")
    fig, ax = evidence_canvas("System Overview")
    steps = ["Generate", "Validate", "Preprocess", "Extract 22 Features", "Train 3 Models", "Export"]
    for i, step in enumerate(steps):
        x = .65 + i * 2.2
        ax.add_patch(FancyBboxPatch((x, 5.55), 1.75, .72, boxstyle="round,pad=.03",
                                   facecolor="#dcecf6", edgecolor="#457b9d"))
        ax.text(x + .875, 5.91, step, ha="center", va="center", fontsize=9.5, fontweight="bold")
        if i < len(steps) - 1: arrow(ax, (x + 1.75, 5.91), (x + 2.16, 5.91))
    values = [("30", "unique samples"), ("90", "measurements"), ("401", "frequency points"), ("0", "sample overlap")]
    for i, (value, label) in enumerate(values):
        x = .65 + i * 3.32
        ax.add_patch(FancyBboxPatch((x, 3.9), 2.7, 1.1, boxstyle="round,pad=.03",
                                   facecolor="#e8f3e8", edgecolor="#4b8063"))
        ax.text(x + 1.35, 4.57, value, ha="center", fontsize=22, fontweight="bold", color="#24553b")
        ax.text(x + 1.35, 4.14, label, ha="center", fontsize=10, color="#36594a")
    table = ax.table(cellText=[[r.model, f"{r.accuracy:.3f}", f"{r.macro_f1:.3f}"] for r in metrics.itertuples()],
                     colLabels=["Model", "Accuracy*", "Macro F1*"], cellLoc="center",
                     bbox=[.2, .17, .6, .23])
    table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.35)
    ax.text(7, .82, "*Synthetic software-demo metrics only — not medical accuracy", ha="center", color="#a13d2d")
    save_evidence(fig, "02_system_overview.png")


def generation_image():
    raw = pd.read_csv(ROOT / "data" / "raw" / "simulated_sparameters.csv")
    fig, ax = evidence_canvas("Simulated Data Generation")
    facts = [("Random seed", "42"), ("Frequency", "1.5–3.0 GHz"), ("Grid", "401 points"),
             ("Samples", str(raw.sample_id.nunique())), ("Measurements", str(raw.measurement_id.nunique())),
             ("Rows", f"{len(raw):,}")]
    for i, (label, value) in enumerate(facts):
        row, col = divmod(i, 3); x, y = .8 + col * 4.45, 5.55 - row * 1.5
        ax.add_patch(FancyBboxPatch((x, y), 3.8, 1.02, boxstyle="round,pad=.03",
                                   facecolor="#e2eff6", edgecolor="#457b9d"))
        ax.text(x + .25, y + .68, label, fontsize=10, color="#48636e")
        ax.text(x + .25, y + .27, value, fontsize=15, fontweight="bold", color="#173b47")
    counts = raw.groupby("label")["sample_id"].nunique()
    chart = fig.add_axes([.18, .1, .64, .25], facecolor="#f7fafb")
    chart.barh(range(len(counts)), counts.values, color=["#6aaed6", "#f2c879", "#df8f8f"])
    chart.set_yticks(range(len(counts)), counts.index); chart.set_xlabel("Unique simulated samples")
    chart.set_xlim(0, max(counts.values) * 1.25)
    for i, value in enumerate(counts.values): chart.text(value + .2, i, str(value), va="center")
    save_evidence(fig, "03_generate_simulated_data.png")


def validation_images():
    from src.data_validation import read_and_validate_csv
    valid_path = ROOT / "sample_data" / "valid_example_1.csv"
    frame, result = read_and_validate_csv(valid_path)
    fig, ax = evidence_canvas("CSV Validation")
    ax.add_patch(FancyBboxPatch((.8, 5.45), 12.4, .78, boxstyle="round,pad=.03",
                               facecolor="#dff3e4", edgecolor="#3d7a50"))
    ax.text(1.15, 5.84, f"PASS: {valid_path.name} — required columns and 401 rows validated", fontsize=12, va="center")
    preview = frame.head(6)[["frequency_ghz", "s11_db", "s21_db", "sample_id", "measurement_id", "label"]].copy()
    preview[["frequency_ghz", "s11_db", "s21_db"]] = preview[["frequency_ghz", "s11_db", "s21_db"]].round(4)
    table = ax.table(cellText=preview.values, colLabels=preview.columns, cellLoc="center", bbox=[.06, .28, .88, .34])
    table.auto_set_font_size(False); table.set_fontsize(8.5)
    ax.text(.8, 1.58, "Validation checks: schema • numeric signals • missing values • label • range • IDs • point count • duplicates", fontsize=10.5)
    ax.text(.8, 1.08, "data_source = SIMULATED", fontsize=12, fontweight="bold", color="#9b4d16")
    save_evidence(fig, "04_csv_validation_success.png")

    messages = [
        ("invalid_missing_s21.csv", "Required column not found: s21_db"),
        ("invalid_non_numeric.csv", "s11_db contains 1 non-numeric value"),
        ("invalid_missing_value.csv", "Missing value detected in s21_db"),
        ("invalid_label.csv", "Unsupported label: Unsupported Label"),
        ("invalid_duplicate_rows.csv", "1 duplicate row reported as a warning"),
        ("invalid_empty.csv", "Empty file reported clearly"),
    ]
    fig, ax = evidence_canvas("CSV Error Handling")
    for i, (name, message) in enumerate(messages):
        y = 6.15 - i * .86
        ax.add_patch(FancyBboxPatch((.75, y - .48), 12.5, .66, boxstyle="round,pad=.02",
                                   facecolor="#fae2e2" if "duplicate" not in name else "#fff0c7",
                                   edgecolor="#a34d4d" if "duplicate" not in name else "#a87b22"))
        ax.text(1.0, y - .04, name, fontsize=10.5, fontweight="bold", va="center")
        ax.text(4.25, y - .04, message, fontsize=9.5, va="center")
    ax.text(.8, .55, "Malformed files produce understandable messages; the application does not crash.", fontsize=10.5, color="#35505b")
    save_evidence(fig, "05_csv_file_errors.png")


def feature_image():
    features = pd.read_csv(ROOT / "data" / "features" / "simulated_features.csv")
    selected = ["measurement_id", "label", "s11_max_db", "s11_min_db", "s11_mean_db",
                "s11_slope", "s21_mean_db", "s21_slope"]
    preview = features[selected].head(12).copy()
    for col in preview.select_dtypes("number"): preview[col] = preview[col].round(4)
    fig, ax = evidence_canvas("Feature Extraction Table — 22 Signal Features")
    table = ax.table(cellText=preview.values, colLabels=preview.columns, cellLoc="center",
                     bbox=[.03, .17, .94, .64])
    table.auto_set_font_size(False); table.set_fontsize(7.8); table.scale(1, 1.22)
    ax.text(7, .67, f"Showing 8 representative columns • Full export: {len(features)} measurements × {len(features.columns)-4} features",
            ha="center", fontsize=10, color="#35505b")
    save_evidence(fig, "07_feature_extraction_table.png")


def prediction_image():
    predictions = pd.read_csv(ROOT / "results" / "predictions.csv")
    row = predictions.iloc[0]
    probability_cols = [c for c in predictions.columns if c.startswith("probability_")]
    fig, ax = evidence_canvas("Prediction — Experimental Sample Group")
    ax.add_patch(FancyBboxPatch((.75, 5.2), 12.5, 1.2, boxstyle="round,pad=.04",
                               facecolor="#dcecf6", edgecolor="#457b9d"))
    ax.text(1.1, 5.95, f"Sample ID: {row.sample_id}     Measurement: {row.measurement_id}     Model: {row.model}", fontsize=11)
    ax.text(1.1, 5.48, f"Predicted synthetic group: {row.predicted_label}", fontsize=17, fontweight="bold", color="#173b47")
    labels = [c.replace("probability_", "") for c in probability_cols]
    values = [float(row[c]) for c in probability_cols]
    chart = fig.add_axes([.2, .22, .62, .27], facecolor="#f7fafb")
    chart.barh(range(len(labels)), values, color=["#6aaed6", "#f2c879", "#78b89a"][:len(labels)])
    chart.set_yticks(range(len(labels)), labels); chart.set_xlim(0, 1); chart.set_xlabel("Model probability")
    for i, value in enumerate(values): chart.text(min(value + .02, .95), i, f"{value:.3f}", va="center")
    fig.text(.5, .08, "Experimental sample-group label only — not a diagnosis and cannot replace a doctor or X-ray",
             ha="center", color="#a13d2d", fontsize=11, fontweight="bold")
    save_evidence(fig, "10_prediction_result.png")


def export_image():
    paths = sorted([p.relative_to(ROOT).as_posix() for folder in ("data", "models", "results", "figures")
                    for p in (ROOT / folder).rglob("*") if p.is_file()])
    fig, ax = evidence_canvas("Exported Research Artifacts")
    groups = [("CSV", [p for p in paths if p.endswith(".csv")]), ("PNG", [p for p in paths if p.endswith(".png")]),
              ("Models", [p for p in paths if p.endswith(".joblib")]), ("Metadata", [p for p in paths if p.endswith(".json")])]
    for i, (title, items) in enumerate(groups):
        x = .7 + (i % 2) * 6.65; y = 5.85 - (i // 2) * 2.7
        ax.add_patch(FancyBboxPatch((x, y - 1.75), 6.0, 2.15, boxstyle="round,pad=.03",
                                   facecolor="#e8eef5", edgecolor="#587184"))
        ax.text(x + .25, y + .08, title, fontsize=13, fontweight="bold", color="#173b47")
        shown = items[:6]
        ax.text(x + .25, y - .28, "\n".join("• " + Path(item).name for item in shown), fontsize=8.7, va="top", linespacing=1.35)
        if len(items) > len(shown): ax.text(x + 4.9, y - 1.42, f"+{len(items)-len(shown)} more", fontsize=8, color="#526b76")
    ax.text(7, .43, "Every exported result is generated from SIMULATED data and accompanied by run metadata.", ha="center", color="#9b4d16")
    save_evidence(fig, "12_export_page.png")


def box(ax, x, y, width, height, title, details, color):
    patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.02",
                           facecolor=color, edgecolor="#264653", linewidth=1.4)
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height * 0.67, title, ha="center", va="center",
            fontsize=11, fontweight="bold", color="#102a32")
    ax.text(x + width / 2, y + height * 0.32, details, ha="center", va="center",
            fontsize=8.5, color="#24444c", linespacing=1.35)


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14,
                                linewidth=1.5, color="#457b9d"))


def architecture_image():
    fig, ax = plt.subplots(figsize=(14, 8), facecolor="#f7fafb")
    ax.set_xlim(0, 14); ax.set_ylim(0, 8); ax.axis("off")
    ax.text(7, 7.55, "BoneWave Software Architecture", ha="center", fontsize=20,
            fontweight="bold", color="#173b47")
    ax.text(7, 7.18, "Research proof-of-concept • SIMULATED DATA ONLY • Not a medical device",
            ha="center", fontsize=10.5, color="#9b4d16")
    box(ax, .5, 5.35, 2.5, 1.25, "Streamlit UI", "10 Thai pages\none-click demo workflow", "#d9edf7")
    box(ax, 3.7, 5.35, 2.5, 1.25, "Input Layer", "Synthetic generator\nCSV import + validation", "#dff3e4")
    box(ax, 6.9, 5.35, 2.5, 1.25, "Signal Pipeline", "preprocessing.py\nfeature_extraction.py", "#fff0c7")
    box(ax, 10.1, 5.35, 3.0, 1.25, "Machine Learning", "Decision Tree • Random Forest • SVM\nStratifiedGroupKFold by sample_id", "#f8dfdf")
    arrow(ax, (3.0, 5.98), (3.7, 5.98)); arrow(ax, (6.2, 5.98), (6.9, 5.98)); arrow(ax, (9.4, 5.98), (10.1, 5.98))
    box(ax, 1.0, 3.15, 3.0, 1.15, "Raw / Processed Data", "data/raw • data/processed\n401 points, 1.5–3.0 GHz", "#e8eef5")
    box(ax, 5.5, 3.15, 3.0, 1.15, "Feature Table", "data/features\n22 S11/S21 features", "#e8eef5")
    box(ax, 10.0, 3.15, 3.0, 1.15, "Evaluation", "Accuracy • Macro F1\nreports • confusion matrices", "#e8eef5")
    arrow(ax, (4.95, 5.35), (2.5, 4.3)); arrow(ax, (8.15, 5.35), (7.0, 4.3)); arrow(ax, (11.6, 5.35), (11.5, 4.3))
    box(ax, 1.0, 1.05, 3.0, 1.15, "Models", "Joblib model files\nfeature metadata + seed", "#e4ddf4")
    box(ax, 5.5, 1.05, 3.0, 1.15, "Figures", "S11/S21 • comparison\nfeature importance • matrices", "#e4ddf4")
    box(ax, 10.0, 1.05, 3.0, 1.15, "Exports", "CSV • PNG • JSON • Joblib\nall marked SIMULATED", "#e4ddf4")
    arrow(ax, (11.5, 3.15), (2.5, 2.2)); arrow(ax, (11.5, 3.15), (7.0, 2.2)); arrow(ax, (11.5, 3.15), (11.5, 2.2))
    fig.tight_layout(); fig.savefig(OUT / "01_software_architecture.png", dpi=180, bbox_inches="tight"); plt.close(fig)


def pytest_image():
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    output = (result.stdout + result.stderr).strip()
    fig, ax = plt.subplots(figsize=(12, 5.5), facecolor="#111827")
    ax.set_facecolor("#111827"); ax.axis("off")
    ax.text(.04, .92, "$ python -m pytest -q", transform=ax.transAxes, color="#93c5fd",
            fontsize=15, family="monospace", fontweight="bold", va="top")
    ax.text(.04, .76, output, transform=ax.transAxes,
            color="#d1fae5" if result.returncode == 0 else "#fecaca", fontsize=13,
            family="monospace", va="top", linespacing=1.55)
    status = "PASS" if result.returncode == 0 else "FAIL"
    ax.text(.96, .08, f"BoneWave test status: {status}", transform=ax.transAxes,
            ha="right", color="#6ee7b7" if result.returncode == 0 else "#fca5a5",
            fontsize=13, family="monospace")
    fig.savefig(OUT / "11_pytest_results.png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor()); plt.close(fig)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def confusion_composite():
    paths = [ROOT / "results" / f"confusion_matrix_{name}.png"
             for name in ("decisiontree", "randomforest", "svm")]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), facecolor="white")
    for ax, path in zip(axes, paths):
        ax.imshow(plt.imread(path)); ax.axis("off")
    fig.suptitle("BoneWave Confusion Matrices — Simulated Data Only", fontsize=17, fontweight="bold")
    fig.tight_layout(); fig.savefig(OUT / "09_confusion_matrices.png", dpi=180, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture_image(); overview_image(); generation_image(); validation_images(); feature_image()
    prediction_image(); export_image(); pytest_image(); confusion_composite()
    shutil.copy2(ROOT / "figures" / "example_s11_s21.png", OUT / "06_s11_s21_graphs.png")
    shutil.copy2(ROOT / "figures" / "model_metric_comparison.png", OUT / "08_model_comparison.png")
    print(f"Report images saved to {OUT}")
