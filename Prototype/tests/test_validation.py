from io import StringIO
import pandas as pd
from src.data_generator import generate_synthetic_data
from src.data_validation import read_and_validate_csv, validate_dataframe


def small_valid(): return generate_synthetic_data(1, 1)


def test_invalid_inputs_report_errors():
    base = small_valid()
    cases = []
    cases.append(base.drop(columns="s21_db"))
    bad_numeric = base.copy(); bad_numeric["s11_db"] = bad_numeric["s11_db"].astype(object); bad_numeric.loc[0, "s11_db"] = "bad"; cases.append(bad_numeric)
    missing = base.copy(); missing.loc[0, "s21_db"] = None; cases.append(missing)
    label = base.copy(); label["label"] = "Unsupported"; cases.append(label)
    for frame in cases:
        assert not validate_dataframe(frame).valid
    assert not read_and_validate_csv(StringIO(""))[1].valid


def test_duplicates_are_reported_without_crashing():
    base = small_valid()
    duplicate = pd.concat([base, base.iloc[[0]]], ignore_index=True)
    result = validate_dataframe(duplicate)
    assert result.valid
    assert any("แถวซ้ำ" in warning for warning in result.warnings)
