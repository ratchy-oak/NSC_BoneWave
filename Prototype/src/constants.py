from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FEATURE_DIR = ROOT / "data" / "features"
MODEL_DIR = ROOT / "models"
RESULT_DIR = ROOT / "results"
FIGURE_DIR = ROOT / "figures"

SEED = 42
FREQUENCY_MIN_GHZ = 1.5
FREQUENCY_MAX_GHZ = 3.0
FREQUENCY_POINTS = 401
LABELS = ["Normal", "Crack Risk", "High Fracture Risk"]
THAI_LABELS = {
    "Normal": "กลุ่มปกติ",
    "Crack Risk": "กลุ่มมีความเสี่ยงต่อรอยร้าว",
    "High Fracture Risk": "กลุ่มมีความเสี่ยงต่อรอยแตกสูง",
}
RAW_COLUMNS = [
    "frequency_ghz", "s11_db", "s21_db", "sample_id",
    "measurement_id", "label", "data_source",
]
DISCLAIMER_TH = (
    "ข้อมูลจำลอง / SIMULATED DATA — ผลทั้งหมดเป็นงานวิจัยต้นแบบและ Proof-of-Concept "
    "ไม่ใช่อุปกรณ์วินิจฉัยทางการแพทย์ ไม่สามารถใช้แทนแพทย์หรือการตรวจ X-ray ได้ "
    "ประสิทธิภาพจากข้อมูลสังเคราะห์ไม่ใช่ประสิทธิภาพทางการแพทย์จริง"
)

def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, FEATURE_DIR, MODEL_DIR, RESULT_DIR, FIGURE_DIR):
        path.mkdir(parents=True, exist_ok=True)
