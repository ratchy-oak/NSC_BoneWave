import pandas as pd
from src.constants import FREQUENCY_MAX_GHZ, FREQUENCY_MIN_GHZ, FREQUENCY_POINTS, RAW_COLUMNS
from src.data_generator import generate_synthetic_data


def test_generation_is_reproducible_and_has_expected_shape():
    first = generate_synthetic_data()
    second = generate_synthetic_data()
    pd.testing.assert_frame_equal(first, second)
    assert list(first.columns) == RAW_COLUMNS
    assert first.sample_id.nunique() == 30
    assert first.measurement_id.nunique() == 90
    assert len(first) == 90 * FREQUENCY_POINTS
    assert first.frequency_ghz.min() == FREQUENCY_MIN_GHZ
    assert first.frequency_ghz.max() == FREQUENCY_MAX_GHZ
    assert first.groupby("measurement_id").size().eq(FREQUENCY_POINTS).all()
    assert set(first.data_source) == {"SIMULATED"}
