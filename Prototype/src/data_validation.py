from __future__ import annotations

from dataclasses import dataclass, field
import pandas as pd

from .constants import FREQUENCY_MAX_GHZ, FREQUENCY_MIN_GHZ, LABELS, RAW_COLUMNS


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_dataframe(df: pd.DataFrame, min_frequency_points: int = 20) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if df.empty:
        return ValidationResult(False, ["ไฟล์ไม่มีข้อมูล (Empty file)"])
    missing_columns = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing_columns:
        return ValidationResult(False, ["ไม่พบคอลัมน์ที่จำเป็น: " + ", ".join(missing_columns)])
    for col in ("frequency_ghz", "s11_db", "s21_db"):
        converted = pd.to_numeric(df[col], errors="coerce")
        bad = converted.isna() & df[col].notna()
        if bad.any():
            errors.append(f"คอลัมน์ {col} มีค่าที่ไม่ใช่ตัวเลข {int(bad.sum())} แถว")
    if df[RAW_COLUMNS].isna().any().any():
        cols = df[RAW_COLUMNS].columns[df[RAW_COLUMNS].isna().any()].tolist()
        errors.append("พบค่าว่างในคอลัมน์: " + ", ".join(cols))
    if not errors:
        freq = pd.to_numeric(df["frequency_ghz"])
        if ((freq < FREQUENCY_MIN_GHZ - 0.1) | (freq > FREQUENCY_MAX_GHZ + 0.1)).any():
            errors.append("ความถี่อยู่นอกช่วงที่รองรับโดยประมาณ 1.4–3.1 GHz")
    bad_labels = sorted(set(df["label"].dropna().astype(str)) - set(LABELS))
    if bad_labels:
        errors.append("ป้ายกำกับไม่รองรับ: " + ", ".join(bad_labels))
    bad_sources = sorted(set(df["data_source"].dropna().astype(str)) - {"SIMULATED"})
    if bad_sources:
        errors.append("รุ่นสาธิตนี้รองรับเฉพาะ data_source = SIMULATED")
    for col in ("sample_id", "measurement_id"):
        if df[col].astype(str).str.strip().eq("").any():
            errors.append(f"คอลัมน์ {col} มีค่าว่าง")
    counts = df.groupby("measurement_id", dropna=False).size()
    if (counts < min_frequency_points).any():
        errors.append(f"การวัดแต่ละชุดต้องมีอย่างน้อย {min_frequency_points} จุดความถี่")
    duplicates = int(df.duplicated().sum())
    if duplicates:
        warnings.append(f"พบแถวซ้ำ {duplicates} แถว")
    return ValidationResult(not errors, errors, warnings)


def read_and_validate_csv(source) -> tuple[pd.DataFrame | None, ValidationResult]:
    try:
        df = pd.read_csv(source)
    except pd.errors.EmptyDataError:
        return None, ValidationResult(False, ["ไฟล์ไม่มีข้อมูล (Empty file)"])
    except Exception as exc:
        return None, ValidationResult(False, [f"ไม่สามารถอ่านไฟล์ CSV: {exc}"])
    return df, validate_dataframe(df)
