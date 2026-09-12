from __future__ import annotations

import json
import platform
from pathlib import Path
import joblib
import matplotlib
import numpy as np
import pandas as pd
import scipy
import sklearn
import streamlit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from .constants import LABELS, MODEL_DIR, RESULT_DIR, SEED, ensure_directories
from .visualization import save_confusion_matrix, save_feature_importance

META_COLUMNS = ["sample_id", "measurement_id", "label", "data_source"]


def group_aware_split(features: pd.DataFrame, seed: int = SEED):
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    positions = np.arange(len(features))
    train_idx, test_idx = next(splitter.split(positions, features["label"], groups=features["sample_id"]))
    train_groups = set(features.iloc[train_idx]["sample_id"])
    test_groups = set(features.iloc[test_idx]["sample_id"])
    if train_groups & test_groups:
        raise RuntimeError("Group-aware split failed: sample overlap detected")
    return train_idx, test_idx


def train_and_evaluate(features: pd.DataFrame, seed: int = SEED, save_outputs: bool = True) -> dict:
    ensure_directories()
    feature_names = [c for c in features.columns if c not in META_COLUMNS]
    X = features[feature_names]
    y = features["label"]
    train_idx, test_idx = group_aware_split(features, seed)
    models = {
        "DecisionTree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=seed),
        "RandomForest": RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=seed, n_jobs=1),
        "SVM": Pipeline([("scaler", StandardScaler()), ("classifier", SVC(probability=True, class_weight="balanced", random_state=seed))]),
    }
    metrics_rows, report_rows, prediction_rows = [], [], []
    fitted = {}
    for name, model in models.items():
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        pred = model.predict(X.iloc[test_idx])
        probabilities = model.predict_proba(X.iloc[test_idx]) if hasattr(model, "predict_proba") else None
        precision, recall, f1, _ = precision_recall_fscore_support(y.iloc[test_idx], pred, average="macro", zero_division=0)
        cm = confusion_matrix(y.iloc[test_idx], pred, labels=LABELS)
        metrics_rows.append({"model": name, "accuracy": accuracy_score(y.iloc[test_idx], pred),
                             "macro_precision": precision, "macro_recall": recall, "macro_f1": f1})
        report = classification_report(y.iloc[test_idx], pred, labels=LABELS, output_dict=True, zero_division=0)
        for label, values in report.items():
            if isinstance(values, dict):
                report_rows.append({"model": name, "class": label, **values})
        for offset, position in enumerate(test_idx):
            row = {"model": name, "sample_id": features.iloc[position]["sample_id"],
                   "measurement_id": features.iloc[position]["measurement_id"],
                   "actual_label": y.iloc[position], "predicted_label": pred[offset], "data_source": "SIMULATED"}
            if probabilities is not None:
                for cls, value in zip(model.classes_, probabilities[offset]): row[f"probability_{cls}"] = value
            prediction_rows.append(row)
        fitted[name] = model
        if save_outputs:
            joblib.dump(model, MODEL_DIR / f"{name.lower()}_simulated.joblib")
            save_confusion_matrix(cm, name, RESULT_DIR / f"confusion_matrix_{name.lower()}.png")
            importance_model = model if hasattr(model, "feature_importances_") else None
            if importance_model is not None:
                save_feature_importance(importance_model, feature_names, name, RESULT_DIR / f"feature_importance_{name.lower()}.png")
    metrics = pd.DataFrame(metrics_rows)
    reports = pd.DataFrame(report_rows)
    predictions = pd.DataFrame(prediction_rows)
    metadata = {
        "data_source": "SIMULATED", "warning": "Research prototype; not medical performance or diagnosis.",
        "features": feature_names, "split_method": "StratifiedGroupKFold (first of 5 folds)", "random_seed": seed,
        "unique_samples": int(features.sample_id.nunique()), "measurements": int(len(features)),
        "train_measurements": int(len(train_idx)), "test_measurements": int(len(test_idx)),
        "train_samples": int(features.iloc[train_idx].sample_id.nunique()),
        "test_samples": int(features.iloc[test_idx].sample_id.nunique()), "sample_overlap": 0,
        "class_distribution": features.label.value_counts().to_dict(),
        "software_versions": {"python": platform.python_version(), "numpy": np.__version__,
                              "pandas": pd.__version__, "scipy": scipy.__version__,
                              "matplotlib": matplotlib.__version__, "scikit_learn": sklearn.__version__,
                              "joblib": joblib.__version__, "streamlit": streamlit.__version__},
    }
    if save_outputs:
        metrics.to_csv(RESULT_DIR / "model_metrics.csv", index=False)
        reports.to_csv(RESULT_DIR / "classification_report.csv", index=False)
        predictions.to_csv(RESULT_DIR / "predictions.csv", index=False)
        (RESULT_DIR / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"metrics": metrics, "reports": reports, "predictions": predictions, "models": fitted,
            "metadata": metadata, "feature_names": feature_names, "train_idx": train_idx, "test_idx": test_idx}
