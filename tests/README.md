# BoneWave — Test Evidence

โฟลเดอร์นี้รวบรวมหลักฐานการทดสอบซอฟต์แวร์สำหรับผู้ตรวจผลงานและ HR พร้อมลิงก์ไปยัง automated tests ที่ใช้งานจริงในแต่ละส่วนของโปรเจกต์

## ผลล่าสุดหลังเพิ่ม E2E และ driver tests — 21 กันยายน 2026

| ชุดทดสอบ | ผ่าน | Statement coverage |
|---|---:|---:|
| BoneWave-AI Python | 41/41 | **94.55%** (`app/`) |
| Prototype Python | 6/6 | 55.85% (`src/`, `scripts/`) |
| Playwright Chromium E2E | 4/4 | ไม่ได้วัด JS coverage |
| **รวม** | **51/51** | ไม่รวม coverage ข้ามขอบเขต |

Browser E2E ประกอบด้วย mock 1 case และ replay ไฟล์วัดจริง Air/Normal/Crack 3 cases จาก `BoneWave-AI/data/real` ผ่าน dashboard/API/WebSocket; ไม่ใช่การวัด hardware ใหม่ และใช้ข้อมูลเดียวกับ reference bank

`device.py` เพิ่มจาก **38.82% เป็น 100% statement coverage** ด้วย fake serial transport; ไม่ใช่ผลตรวจอุปกรณ์จริง ไม่มี failed หรือ skipped cases ในการรันสำเร็จล่าสุด

- [รายงานล่าสุด ภาพหน้าจอ และ Playwright trace](evidence/2026-09-21/README.md)
- [Test plan และ requirement → test case](TEST_PLAN.md)
- [วิธีบันทึก bug ใน GitHub Issues](BUG_TRACKING.md)

## ตรวจผลล่าสุดและรันซ้ำ

หลักฐานที่เก็บถาวรอยู่ใน `tests/evidence/` ส่วน `test-results/latest/` เป็นผลชั่วคราวที่คำสั่งทดสอบสร้างใหม่ได้ และไม่เก็บใน Git

[GitHub Actions — BoneWave tests](https://github.com/ratchy-oak/NSC_BoneWave/actions/workflows/tests.yml) จะรันทดสอบแยกสองส่วนเมื่อ push หรือเปิด pull request หลัง workflow นี้ถูก push ขึ้น GitHub สำเร็จ แต่ละ run มี artifacts ได้แก่ JUnit XML, coverage รายโมดูล, summary JSON และเวอร์ชัน dependencies จริง ตัวเลขด้านล่างเป็น snapshot ไม่ใช่ตัวเลขที่ปรับเองตาม CI

หลังติดตั้ง dependencies ของส่วนที่ต้องการและ `coverage==7.16.1` ให้รันจาก root:

```sh
python tests/run_tests.py --component BoneWave-AI
python tests/run_tests.py --component Prototype
```

ควรใช้ environment แยกสำหรับแต่ละส่วนตามวิธีติดตั้งด้านล่าง หาก environment มี dependencies ครบทั้งสองส่วน สามารถใช้ `python tests/run_tests.py` เพื่อรันทั้งคู่ได้ ตัว runner ใช้สำเนาชั่วคราวและบันทึกผลล่าสุดลง `test-results/latest/` ไม่แก้ข้อมูลต้นฉบับ ผล failed tests ทำให้คำสั่งและ CI ล้มเหลว จำนวน tests และ coverage คำนวณจากการรันจริง ไม่มีการกำหนดให้แสดง 33 หรือ 85% ตายตัว

## ผลทดสอบเดิมก่อนเพิ่ม E2E และ driver tests

ผลรันวันที่ **20 กันยายน 2026** ด้วย Python 3.12 และ pytest 9.0.2 บนสำเนาของ working tree ณ เวลาตรวจสอบ เป็นผลของการรันครั้งนั้น ไม่ใช่สถานะ CI ของทุก commit

| ส่วนของระบบ | Test cases | Passed | Failed | Python statement coverage |
|---|---:|---:|---:|---:|
| BoneWave-AI | 27 | 27 | 0 | 85.10% (531/624 statements) |
| Prototype | 6 | 6 | 0 | 55.85% (296/530 statements) |
| **รวม** | **33** | **33** | **0** | แยกตามขอบเขตข้างต้น |

- BoneWave-AI: วัด Python ใน `app/` ไม่รวม JavaScript/CSS ของหน้าเว็บ
- Prototype: วัด `src/` และ `scripts/` ไม่รวม Streamlit `app.py`
- Coverage ข้างต้นไม่ใช่ branch coverage หรือสัดส่วน requirements ที่ทดสอบครบ
- ไม่พบบันทึกจำนวน bug และระดับความรุนแรงที่ใช้ยืนยันย้อนหลังได้; จำนวน failed tests เป็น 0 ไม่ได้หมายถึงระบบไม่มี bug

## ชุดทดสอบเดิม (ก่อนเพิ่ม driver tests และ E2E)

| ชุดทดสอบ | จำนวน cases | สิ่งที่ตรวจสอบ |
|---|---:|---|
| [API และ UI assertions](../BoneWave-AI/tests/test_api.py) | 8 | Health, model information, การเชื่อมต่อซ้ำ, reference status, endpoint และข้อความ/องค์ประกอบใน HTML/JavaScript |
| [Touchstone parser](../BoneWave-AI/tests/test_touchstone.py) | 5 | รูปแบบ RI/MA/DB, interpolation และข้อมูลผิดรูปแบบ |
| [Live acquisition](../BoneWave-AI/tests/test_live.py) | 14 | Mock device, WebSocket, stopping/cancellation, error recovery, protocol, stabilization และ reference bank |
| [Prototype pipeline](../Prototype/tests/) | 6 | การสร้างข้อมูลซ้ำได้, validation, feature extraction, group-aware split และ pipeline outputs |

จำนวน cases นับหลังขยาย pytest parametrization แล้ว การตรวจข้อความ UI ไม่ใช่การทดสอบการใช้งานผ่าน browser แบบ end-to-end

## รายงานจากการรัน

- [รายละเอียด environment และวิธีวัด](evidence/2026-09-20/README.md)
- BoneWave-AI: [coverage แยกแต่ละโมดูล](evidence/2026-09-20/BoneWave-AI-coverage.txt) · [JUnit XML](evidence/2026-09-20/BoneWave-AI-junit.xml)
- Prototype: [coverage แยกแต่ละโมดูล](evidence/2026-09-20/Prototype-coverage.txt) · [JUnit XML](evidence/2026-09-20/Prototype-junit.xml)

## วิธีรันทดสอบ

ใช้ Python 3.12 และแยก virtual environment ของแต่ละส่วน เพราะเวอร์ชัน dependencies ต่างกัน แนะนำให้รันบนสำเนาโปรเจกต์: บาง tests สร้างไฟล์ผลลัพธ์และเปลี่ยนสถานะ live references

### BoneWave-AI

จาก root ของ repository:

```sh
cd BoneWave-AI
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt coverage==7.16.1
python -m coverage run --source=app -m pytest -q --junitxml=junit.xml
python -m coverage report --precision=2
```

### Prototype

เปิด terminal ใหม่ที่ root ของ repository:

```sh
cd Prototype
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt coverage==7.16.1
python -m coverage run --source=src,scripts -m pytest -q --junitxml=junit.xml
python -m coverage report --precision=2
```

บน Windows Command Prompt ใช้ `.venv\Scripts\activate` แทน `source .venv/bin/activate` ผลอาจแตกต่างตาม runtime/dependencies; environment ของผลที่แนบระบุไว้ในรายงาน

## ขอบเขตของหลักฐาน

การรันนี้ไม่ได้ทดสอบกับ NanoVNA จริง; acquisition tests ใช้อุปกรณ์จำลอง ข้อมูลของ Prototype เป็นข้อมูลสังเคราะห์ ผลทดสอบซอฟต์แวร์และ coverage ไม่ใช่หลักฐานความแม่นยำทางคลินิก และไม่ใช่ผลการประเมินกับผู้ป่วย
