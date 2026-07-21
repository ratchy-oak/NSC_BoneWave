# คู่มือติดตั้ง BoneWave

> ข้อมูลและผลทั้งหมดเป็นข้อมูลจำลองสำหรับ research proof-of-concept ไม่ใช่อุปกรณ์วินิจฉัย

## Windows

1. ติดตั้ง Python 3.11+ และเลือก Add Python to PATH
2. เปิด Command Prompt ในโฟลเดอร์โครงการ
3. รัน `python -m venv .venv`
4. รัน `.venv\Scripts\activate`
5. รัน `python -m pip install --upgrade pip`
6. รัน `python -m pip install -r requirements.txt`
7. รัน `python scripts\run_pipeline.py` เพื่อตรวจ pipeline
8. เปิด UI ด้วย `run_app.bat` หรือ `python -m streamlit run app.py`

## macOS/Linux

1. ตรวจ `python3 --version` (3.11+)
2. รัน `python3 -m venv .venv && source .venv/bin/activate`
3. รัน `python -m pip install --upgrade pip`
4. รัน `python -m pip install -r requirements.txt`
5. รัน `python scripts/run_pipeline.py`
6. รัน `./run_app.sh` หรือ `python -m streamlit run app.py`

หาก port 8501 ถูกใช้ เพิ่ม `--server.port 8502` และหาก cache ของ Matplotlib เขียนไม่ได้ให้ตั้ง `MPLCONFIGDIR` ไปยังโฟลเดอร์ชั่วคราวที่เขียนได้
