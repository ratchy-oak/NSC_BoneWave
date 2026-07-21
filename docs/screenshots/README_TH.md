# ชุดภาพหลักฐาน BoneWave

ภาพทุกภาพสร้างจากข้อมูลและผลลัพธ์จริงของโปรแกรม แต่ข้อมูลต้นทางทั้งหมดเป็น **SIMULATED DATA** สำหรับ research proof-of-concept ไม่ใช่ผลผู้ป่วยหรือประสิทธิภาพทางการแพทย์

| ลำดับ | ไฟล์ | คำบรรยายแนะนำ |
|---|---|---|
| 1 | `01_software_architecture.png` | สถาปัตยกรรมซอฟต์แวร์ BoneWave ตั้งแต่ Streamlit UI ถึงการส่งออกผลลัพธ์ |
| 2 | `02_system_overview.png` | ภาพรวม pipeline จำนวน sample/measurement และ synthetic model metrics |
| 3 | `03_generate_simulated_data.png` | การสร้างข้อมูล S11/S21 สังเคราะห์ด้วย seed 42 |
| 4 | `04_csv_validation_success.png` | ตัวอย่าง CSV ที่ผ่านการตรวจสอบ schema และค่าที่จำเป็น |
| 5 | `05_csv_file_errors.png` | การจัดการไฟล์ผิดรูปแบบโดยไม่ทำให้โปรแกรมหยุดทำงาน |
| 6 | `06_s11_s21_graphs.png` | กราฟ S11 และ S21 ของ measurement สังเคราะห์หนึ่งชุด |
| 7 | `07_feature_extraction_table.png` | ตัวอย่างตาราง numerical features จาก S11/S21 |
| 8 | `08_model_comparison.png` | เปรียบเทียบสามโมเดลบน synthetic dataset ด้วย group-aware split |
| 9 | `09_confusion_matrices.png` | Confusion Matrix ของ Decision Tree, Random Forest และ SVM |
| 10 | `10_prediction_result.png` | ตัวอย่าง predicted experimental sample group และ probability |
| 11 | `11_pytest_results.png` | ผลทดสอบอัตโนมัติ `6 passed` จากการรันจริง |
| 12 | `12_export_page.png` | รายการ CSV, PNG, Joblib และ metadata ที่ระบบส่งออก |

ห้ามใช้คำบรรยายที่สื่อว่า Accuracy/F1-score เป็นความแม่นยำทางการแพทย์ และ Prediction ไม่ใช่คำวินิจฉัย
