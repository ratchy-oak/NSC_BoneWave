# หลักฐานสำหรับรายงาน BoneWave

## ข้อเท็จจริงของระบบ

`data_generator` สร้าง S11/S21 สังเคราะห์ 1.5–3.0 GHz จำนวน 401 จุด; `data_validation` ตรวจ schema/ค่า; `preprocessing` เรียง interpolate และ smooth แบบเลือกได้; `feature_extraction` สร้าง 22 features; `modeling` แบ่ง sample แบบ group-aware และประเมินสามโมเดล; `visualization` สร้าง PNG; `export_utils` ช่วยส่งออก ทุกส่วนเป็น software demonstration ไม่มีข้อมูลผู้ป่วยหรือ NanoVNA จริง

## ขั้นตอนทดสอบที่ทำซ้ำได้

```bash
python -m compileall .
pytest -q
python scripts/run_pipeline.py
python -m streamlit run app.py --server.headless true
```

## Functional test cases

| รหัส | ขั้นตอน | ผลที่คาดหวัง |
|---|---|---|
| F01 | สร้างข้อมูล seed 42 สองครั้ง | ตารางตรงกันทุกค่า |
| F02 | ตรวจ CSV ถูกต้อง | ผ่านและไม่ crash |
| F03 | ลบ S21 / ใส่ text / null / label ผิด | แสดง error ภาษาไทย |
| F04 | ทำแถวซ้ำ | แสดง warning จำนวนแถว |
| F05 | สกัด linear signal | slope/min/max ตรงค่าคาดหมาย |
| F06 | แบ่ง train/test | `sample_id` overlap = 0 |
| F07 | ฝึกสามโมเดล | เกิด metrics/report/models/confusion matrices |
| F08 | one-click workflow | pipeline ครบและแสดง example prediction |
| F09 | export | ดาวน์โหลดไฟล์ได้และ metadata ระบุ SIMULATED |

## Software versions และ outputs

รุ่นที่ validate ระบุใน `requirements.txt`; รุ่น runtime จริงถูกบันทึกใน `results/run_metadata.json` ผลหลักอยู่ใน `data/raw`, `data/processed`, `data/features`, `models`, `results`, และ `figures` ค่าที่รายงานต้องคัดจากไฟล์เหล่านี้หลังรันจริง ห้ามแต่งตัวเลข

## Suggested figure captions

- “สัญญาณ S11 และ S21 สังเคราะห์ของตัวอย่างหนึ่งชุด ใช้เพื่อทดสอบซอฟต์แวร์ ไม่ใช่การวัดจริง”
- “ค่าเฉลี่ยสัญญาณสังเคราะห์แยกตาม experimental sample-group label”
- “การเปรียบเทียบโมเดลบน synthetic dataset ด้วย group-aware split; ไม่ใช่ medical accuracy”
- “Confusion Matrix จากข้อมูลสังเคราะห์ โดย train/test ไม่มี physical sample ID ซ้ำกัน”

## จุดแทรกภาพ

แทรกภาพตามลำดับใน `SCREENSHOT_CHECKLIST_TH.md` หลังหัวข้อ UI, validation, signal analysis, ML evaluation และ limitations โดยใช้ภาพหน้าจอจากการรันจริง ไม่ใช้ภาพว่างหรือภาพจำลองหน้าจอ

## ข้อความอธิบายที่ปลอดภัย

“BoneWave รุ่นนี้สาธิตความเป็นไปได้ของ software pipeline ด้วยสัญญาณสังเคราะห์สำหรับตรวจสอบการไหลของข้อมูล การสกัดคุณลักษณะ และการเปรียบเทียบ Machine Learning เท่านั้น ผลไม่แสดงความแม่นยำทางคลินิกและไม่สามารถใช้วินิจฉัยหรือแทนการประเมินโดยแพทย์และ X-ray”
