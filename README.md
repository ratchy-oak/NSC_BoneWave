# BoneWave

**ข้อมูลจำลอง / SIMULATED DATA** — BoneWave เป็น research proof-of-concept สำหรับสาธิต software pipeline ของสัญญาณ S11/S21 เท่านั้น สัญญาณ ป้ายกลุ่ม prediction และ metrics ทั้งหมดเป็นข้อมูลสังเคราะห์ ไม่ใช่ผลจากผู้ป่วย การทดลองจริง หรือ NanoVNA และห้ามนำเสนอเป็น medical performance โปรแกรมไม่ใช่อุปกรณ์วินิจฉัยและใช้แทนแพทย์หรือ X-ray ไม่ได้

## ความสามารถ

สร้างข้อมูลซ้ำได้ด้วย seed 42, นำเข้าและตรวจ CSV, preprocessing แบบโปร่งใส, สกัด 22 features, เปรียบเทียบ Decision Tree / Random Forest / SVM ด้วย `StratifiedGroupKFold`, แสดงกราฟและ prediction กลุ่มทดลอง และส่งออก CSV/PNG/Joblib/JSON โดย train/test ไม่มี `sample_id` ซ้ำกัน

## ติดตั้ง

ต้องใช้ Python 3.11 ขึ้นไป

```bash
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate          # Windows
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## เรียกใช้งาน

```bash
python scripts/run_pipeline.py
python -m streamlit run app.py
```

หรือ `./run_app.sh` บน macOS/Linux และ `run_app.bat` บน Windows

## รูปแบบ CSV

Long form: `frequency_ghz,s11_db,s21_db,sample_id,measurement_id,label,data_source` ป้ายที่รองรับคือ `Normal`, `Crack Risk`, `High Fracture Risk`; สำหรับรุ่นนี้ `data_source` ต้องสื่อว่าเป็น `SIMULATED` ตัวอย่างอยู่ใน `sample_data/`

## โครงสร้างสำคัญ

- `app.py` — Streamlit UI ภาษาไทย 10 หน้า
- `src/` — generator, validation, preprocessing, features, modeling, visualization, export
- `scripts/run_pipeline.py` — pipeline แบบไม่ใช้ UI
- `tests/` — unit/integration tests
- `data/`, `models/`, `results/`, `figures/` — outputs
- `docs/` — คู่มือและหลักฐานรายงานภาษาไทย

## ทดสอบ

```bash
python -m compileall .
pytest -q
python scripts/run_pipeline.py
```

## แก้ปัญหา

- `ModuleNotFoundError`: activate `.venv` และติดตั้ง `requirements.txt` ใหม่
- Streamlit port ถูกใช้: `python -m streamlit run app.py --server.port 8502`
- CSV ไม่ผ่าน: ตรวจชื่อคอลัมน์ ค่าว่าง ตัวเลข label และอย่างน้อย 20 frequency points ต่อ measurement
- Matplotlib cache permission: ตั้ง `MPLCONFIGDIR` เป็นโฟลเดอร์ที่เขียนได้

รายละเอียดเพิ่ม: [คู่มือติดตั้ง](docs/INSTALLATION_MANUAL_TH.md) และ [คู่มือผู้ใช้](docs/USER_MANUAL_TH.md)
