# อธิบายงานทดสอบ BoneWave ในการสัมภาษณ์

คำอธิบายนี้อ้างอิงสิ่งที่ตรวจได้ในโค้ด ส่วนบทบาทส่วนตัวและประสบการณ์ใช้อุปกรณ์จริงให้อธิบายตามงานที่ทำจริง

## ทำไมใช้ Mock NanoVNA?

“ผมใช้ mock ใน automated tests เพื่อควบคุมข้อมูลและจำลองข้อผิดพลาดได้ซ้ำ โดยไม่ต้องต่ออุปกรณ์ทุกครั้ง เช่น ตรวจว่าระบบหยุดรับข้อมูลและปล่อยการเชื่อมต่อเมื่อเกิด error หรือหยุดหลังครบจำนวน sweeps การทดสอบนี้ตรวจ software logic ส่วนการสื่อสารกับ firmware, สายสัญญาณ และคุณภาพการวัดจริงต้องทดสอบกับ hardware แยก”

หลักฐาน: [test_live.py](../BoneWave-AI/tests/test_live.py) โดยเฉพาะ `test_release_after_errors`, `test_one_sample_scan_stops_after_configured_sweeps` และ `test_v2_binary_protocol_commands_and_fifo` การทดสอบ protocol ใช้ข้อมูล binary ที่สร้างขึ้น ไม่ได้ยืนยันการทำงานกับอุปกรณ์จริง

## Coverage ล่าสุดหมายถึงอะไร และ UI ทดสอบอย่างไร?

“หลังเพิ่ม driver tests ผลรัน 21 กันยายน 2026 ได้ Python statement coverage ของ BoneWave-AI/app 590 จาก 624 statements หรือ 94.55% เพิ่มจาก 85.10% ส่วน device.py เพิ่มจาก 38.82% เป็น 100% ด้วย fake serial transport ที่ตรวจ success path, fragmented reads, timeout และ error handling”

“ผมเพิ่ม Playwright E2E 1 case ให้ Chromium เปิด dashboard จริง กดเชื่อมต่อ MOCK เปิดและปิดหน้าต่าง setup แล้วสแกนผ่าน API/WebSocket จริง ตรวจครบ 3 sweeps ผลที่แสดงตรงกับ backend และ disconnect สำเร็จ โดยไม่ stub network responses”

หลักฐาน: [รายงานล่าสุด](evidence/2026-09-21/README.md), [driver tests](../BoneWave-AI/tests/test_device.py), [browser test](e2e/test_dashboard.py)

Python coverage ไม่รวม JavaScript และไม่ได้รวม server subprocess ของ E2E การทดสอบ browser นี้ตรวจ behavior ไม่ได้วัด JS coverage และยังไม่ครอบคลุม Streamlit UI หรือ hardware จริง การได้ 100% statement coverage ไม่ได้แปลว่าทุก branch หรือทุกสภาพอุปกรณ์ถูกทดสอบแล้ว

## ตรวจ train/test overlap อย่างไร?

“ใน Prototype ผมแบ่งด้วย StratifiedGroupKFold โดยใช้ sample_id เป็นกลุ่ม เพื่อให้ measurements ของ sample เดียวกันอยู่ฝั่งเดียวกัน จากนั้นแปลง sample_id ของ train และ test เป็น sets และตรวจว่าไม่มีสมาชิกซ้ำกัน ทั้งในโค้ดและ automated test”

หลักฐาน:

- [group_aware_split](../Prototype/src/modeling.py): ใช้ `groups=features['sample_id']` และตรวจ intersection; ถ้าซ้ำจะ raise RuntimeError
- [test_group_split_and_all_models_train](../Prototype/tests/test_modeling.py): ตรวจ `isdisjoint` จาก indices ที่แบ่งจริง
- [test_complete_pipeline_creates_required_outputs](../Prototype/tests/test_pipeline.py): ตรวจ outputs และ metadata `sample_overlap == 0`

ค่า metadata ถูกกำหนดเป็น 0 หลังผ่าน guard; หลักฐานการไม่ overlap จึงอยู่ที่การตรวจ sets ด้วย ไม่ใช่การอ่าน metadata เพียงอย่างเดียว ปัจจุบันใช้ผลแบ่งแรกจาก 5 folds ไม่ได้รายงานค่าเฉลี่ยการประเมินทุก fold และเป็นข้อมูลสังเคราะห์ ไม่ใช่ผลความแม่นยำทางคลินิก

## จำนวน tests และ bug อธิบายอย่างไร?

“ผลล่าสุดคือ BoneWave-AI Python 41 cases, Prototype 6 cases และ Chromium E2E 1 case รวม 48 cases ผ่านทั้งหมด ไม่พบ skipped cases โดยนับ pytest cases หลังขยาย parametrization จำนวนนี้ไม่ใช่จำนวน bugs ที่เคยพบ”

เพิ่มแบบฟอร์ม GitHub Issues และ [วิธีบันทึก defect](BUG_TRACKING.md) แล้ว แต่ยังไม่มีตัวเลข defect ที่ยืนยันจาก issue records ในงานนี้ ให้บันทึกเมื่อ reproduce ปัญหาจริงได้ พร้อมแนบ evidence และ regression test

## ข้อความสำหรับ CV

> พัฒนาและทดสอบ BoneWave ด้วย automated tests 48 cases ผ่านทั้งหมด รวม Playwright/Chromium E2E สำหรับ workflow เชื่อมต่อ–สแกน–แสดงผล–ตัดการเชื่อมต่อ ผ่าน Mock NanoVNA เพิ่ม Python backend statement coverage จาก 85.10% เป็น 94.55% และ device.py จาก 38.82% เป็น 100% ด้วย driver tests พร้อมจัดทำ requirement-to-test traceability และ GitHub Actions workflow (ผลรันในเครื่อง 21 ก.ย. 2026)

ใช้ข้อความเมื่อบทบาทตรงกับงานที่ทำจริง Workflow จะมีผลรันบน GitHub หลัง push; ผลปัจจุบันยืนยันจากการรันในเครื่อง ตรวจผลใหม่และปรับตัวเลข CV เมื่อชุดทดสอบเปลี่ยน
