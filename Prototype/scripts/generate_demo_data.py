#!/usr/bin/env python3
from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.constants import RAW_DIR, ensure_directories
from src.data_generator import generate_synthetic_data

ensure_directories()
data = generate_synthetic_data()
data.to_csv(RAW_DIR / "simulated_sparameters.csv", index=False)
sample_dir = ROOT / "sample_data"
sample_dir.mkdir(exist_ok=True)
for number, measurement_id in enumerate(data.measurement_id.unique()[:3], start=1):
    data[data.measurement_id == measurement_id].to_csv(sample_dir / f"valid_example_{number}.csv", index=False)
base = data[data.measurement_id == data.measurement_id.iloc[0]].copy()
base.drop(columns="s21_db").to_csv(sample_dir / "invalid_missing_s21.csv", index=False)
base.assign(s11_db=base.s11_db.astype(object)).pipe(
    lambda frame: frame.assign(s11_db=frame.s11_db.mask(frame.index == frame.index[0], "not-a-number"))
).to_csv(sample_dir / "invalid_non_numeric.csv", index=False)
base.assign(label="Unsupported Label").to_csv(sample_dir / "invalid_label.csv", index=False)
base.assign(s21_db=base.s21_db.mask(base.index == base.index[0])).to_csv(sample_dir / "invalid_missing_value.csv", index=False)
pd_duplicate = pd.concat([base, base.iloc[[0]]], ignore_index=True)
pd_duplicate.to_csv(sample_dir / "invalid_duplicate_rows.csv", index=False)
(sample_dir / "invalid_empty.csv").write_text("", encoding="utf-8")
print(f"Saved {len(data):,} simulated rows to {RAW_DIR / 'simulated_sparameters.csv'}")
