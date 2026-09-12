import numpy as np,pytest
from pathlib import Path
from app.touchstone import parse_touchstone,load_standard_trace,TouchstoneError,TARGET_FREQUENCIES
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize("fmt,row,expected",[("RI","1 0 0 3 4 0 0 0 0",5),("MA","1 0 0 2 90 0 0 0 0",2),("DB","1 0 0 20 0 0 0 0 0",10)])
def test_formats(fmt,row,expected):
    t=parse_touchstone(f"# GHZ S {fmt} R 50\n{row}\n2 0 0 1 0 0 0 0 0");assert abs(t.s21[0])==pytest.approx(expected)
def test_extract_and_interpolate():
    t=load_standard_trace(ROOT/"data"/"real"/"normal"/"Normal_002.s2p");assert len(t.frequency_hz)==404;assert np.array_equal(t.frequency_hz,TARGET_FREQUENCIES);assert np.isfinite(t.s21_db).all()
def test_malformed():
    with pytest.raises(TouchstoneError):parse_touchstone("# HZ S RI R 50\n1 2")
