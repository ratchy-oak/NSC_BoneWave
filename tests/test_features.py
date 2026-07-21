import numpy as np
import pandas as pd
from src.feature_extraction import extract_features


def test_known_linear_signal_features():
    frequency = np.linspace(1.5, 3.0, 401)
    frame = pd.DataFrame({"frequency_ghz": frequency, "s11_db": 2 * frequency + 1,
                          "s21_db": -3 * frequency + 4, "sample_id": "S1",
                          "measurement_id": "M1", "label": "Normal", "data_source": "SIMULATED"})
    row = extract_features(frame).iloc[0]
    assert np.isclose(row.s11_slope, 2.0)
    assert np.isclose(row.s21_slope, -3.0)
    assert np.isclose(row.s11_max_db, 7.0)
    assert np.isclose(row.s11_min_frequency_ghz, 1.5)
    assert np.isclose(row.s21_min_frequency_ghz, 3.0)
