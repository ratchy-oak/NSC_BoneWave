from src.data_generator import generate_synthetic_data
from src.feature_extraction import extract_features
from src.modeling import group_aware_split, train_and_evaluate


def test_group_split_and_all_models_train(tmp_path):
    features = extract_features(generate_synthetic_data())
    train, test = group_aware_split(features)
    assert set(features.iloc[train].sample_id).isdisjoint(set(features.iloc[test].sample_id))
    result = train_and_evaluate(features, save_outputs=False)
    assert set(result["models"]) == {"DecisionTree", "RandomForest", "SVM"}
    assert len(result["metrics"]) == 3
    assert result["metadata"]["sample_overlap"] == 0
