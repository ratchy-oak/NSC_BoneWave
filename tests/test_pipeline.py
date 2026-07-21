from pathlib import Path
from scripts.run_pipeline import run_pipeline


def test_complete_pipeline_creates_required_outputs():
    result = run_pipeline()
    required = ["data/raw/simulated_sparameters.csv", "data/processed/simulated_sparameters_processed.csv",
                "data/features/simulated_features.csv", "results/model_metrics.csv",
                "results/classification_report.csv", "results/predictions.csv", "results/run_metadata.json",
                "results/confusion_matrix_decisiontree.png", "results/confusion_matrix_randomforest.png",
                "results/confusion_matrix_svm.png", "models/decisiontree_simulated.joblib",
                "models/randomforest_simulated.joblib", "models/svm_simulated.joblib"]
    assert all(Path(path).exists() and Path(path).stat().st_size > 0 for path in required)
    assert result["metadata"]["sample_overlap"] == 0
