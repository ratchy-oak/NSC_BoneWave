# อธิบายงานทดสอบ BoneWave ในการสัมภาษณ์

คำอธิบายนี้อ้างอิงสิ่งที่ตรวจได้ในโค้ด ส่วนบทบาทส่วนตัวและประสบการณ์ใช้อุปกรณ์จริงให้อธิบายตามงานที่ทำจริง

## ทำไมใช้ Mock NanoVNA?

“ผมใช้ mock ใน automated tests เพื่อควบคุมข้อมูลและจำลองข้อผิดพลาดได้ซ้ำ โดยไม่ต้องต่ออุปกรณ์ทุกครั้ง เช่น ตรวจว่าระบบหยุดรับข้อมูลและปล่อยการเชื่อมต่อเมื่อเกิด error หรือหยุดหลังครบจำนวน sweeps การทดสอบนี้ตรวจ software logic ส่วนการสื่อสารกับ firmware, สายสัญญาณ และคุณภาพการวัดจริงต้องทดสอบกับ hardware แยก”

หลักฐาน: [test_live.py](../BoneWave-AI/tests/test_live.py) โดยเฉพาะ `test_release_after_errors`, `test_one_sample_scan_stops_after_configured_sweeps` และ `test_v2_binary_protocol_commands_and_fifo` การทดสอบ protocol ใช้ข้อมูล binary ที่สร้างขึ้น ไม่ได้ยืนยันการทำงานกับอุปกรณ์จริง

## Coverage 85% หมายถึงอะไร และทำไมไม่รวม UI?

“ผล snapshot ที่ติดวันที่ 20 กรกฎาคม 2026 (วันที่ปรับแก้ภายหลัง; รันจริง 20 กันยายน 2026) วัด statement coverage ของ Python ใน BoneWave-AI/app ได้ 531 จาก 624 statements หรือ 85.10% เครื่องมือ coverage.py เก็บการทำงานของ Python; JavaScript ต้องใช้เครื่องมือและ browser tests เพิ่ม ส่วน Streamlit app.py อยู่ใน Prototype และไม่ได้อยู่ในขอบเขต src/scripts ของการรันนั้น ผมจึงระบุขอบเขตทุกครั้ง ไม่อ้างว่า 85% ครอบคลุมทั้งระบบ”

หลักฐาน: [รายงานแยกโมดูล](evidence/2026-07/BoneWave-AI-coverage.txt) ข้อจำกัดที่เห็นชัดคือ `app/nanovna/device.py` ได้ 38.82% แม้บางส่วน เช่น acquisition จะได้ 100% และ UI tests ปัจจุบันตรวจข้อความ HTML/JavaScript ไม่ใช่ browser end-to-end tests

## ตรวจ train/test overlap อย่างไร?

“ใน Prototype ผมแบ่งด้วย StratifiedGroupKFold โดยใช้ sample_id เป็นกลุ่ม เพื่อให้ measurements ของ sample เดียวกันอยู่ฝั่งเดียวกัน จากนั้นแปลง sample_id ของ train และ test เป็น sets และตรวจว่าไม่มีสมาชิกซ้ำกัน ทั้งในโค้ดและ automated test”

หลักฐาน:

- [group_aware_split](../Prototype/src/modeling.py): ใช้ `groups=features['sample_id']` และตรวจ intersection; ถ้าซ้ำจะ raise RuntimeError
- [test_group_split_and_all_models_train](../Prototype/tests/test_modeling.py): ตรวจ `isdisjoint` จาก indices ที่แบ่งจริง
- [test_complete_pipeline_creates_required_outputs](../Prototype/tests/test_pipeline.py): ตรวจ outputs และ metadata `sample_overlap == 0`

ค่า metadata ถูกกำหนดเป็น 0 หลังผ่าน guard; หลักฐานการไม่ overlap จึงอยู่ที่การตรวจ sets ด้วย ไม่ใช่การอ่าน metadata เพียงอย่างเดียว ปัจจุบันใช้ผลแบ่งแรกจาก 5 folds ไม่ได้รายงานค่าเฉลี่ยการประเมินทุก fold และเป็นข้อมูลสังเคราะห์ ไม่ใช่ผลความแม่นยำทางคลินิก

## 33 tests และจำนวน bug อธิบายอย่างไร?

“ผล snapshot คือ BoneWave-AI 27 cases และ Prototype 6 cases รวม 33 cases ผ่านทั้งหมด โดยนับหลังขยาย parametrization จำนวนนี้เป็น cases ในชุดทดสอบ ไม่ใช่จำนวน bugs ที่เคยพบ ผมยังไม่มี defect log ที่ใช้สรุปจำนวน bugs ย้อนหลังได้”

เมื่อแก้ tests ให้ตรวจรายงานล่าสุดใน GitHub Actions และอัปเดตตัวเลข CV ตามผลรัน โดยเก็บวันที่และขอบเขตของตัวเลขไว้ด้วย

## ข้อความสำหรับ CV

> พัฒนาและทดสอบ BoneWave ด้วย automated tests 33 cases ผ่านทั้งหมด พร้อม Python statement coverage 85.10% ในส่วน BoneWave-AI backend ครอบคลุม API, WebSocket, Touchstone parsing และ acquisition logic ผ่าน Mock NanoVNA; ตรวจการแบ่งข้อมูลสังเคราะห์ของ Prototype ให้ train/test ไม่มี sample_id ซ้ำกัน (รายงานติดวันที่ 20 ก.ค. 2026 โดยปรับแก้ภายหลัง; รันจริง 20 ก.ย. 2026)

ใช้ข้อความนี้เมื่อบทบาท “พัฒนาและทดสอบ” ตรงกับงานส่วนตัวที่ทำจริง และอัปเดตตัวเลขหากอ้างอิงผลรันใหม่
