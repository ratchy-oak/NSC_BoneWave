from __future__ import annotations

from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.constants import (DISCLAIMER_TH, FEATURE_DIR, FIGURE_DIR, MODEL_DIR, PROCESSED_DIR,
                           RAW_DIR, RESULT_DIR, THAI_LABELS, ensure_directories)
from src.data_generator import generate_synthetic_data
from src.data_validation import read_and_validate_csv, validate_dataframe
from src.export_utils import csv_bytes, json_bytes
from src.feature_extraction import extract_features
from src.modeling import train_and_evaluate
from src.preprocessing import preprocess_data
from src.visualization import (figure_to_png, plot_average_by_class, plot_class_distribution,
                               plot_measurement, plot_metric_comparison)

st.set_page_config(page_title="BoneWave", page_icon="🦴", layout="wide")
ensure_directories()

st.markdown("""<style>
.sim-badge{display:inline-block;background:#fff3cd;color:#6d5100;border:1px solid #e5c75b;
padding:.35rem .7rem;border-radius:999px;font-weight:700;margin-bottom:.6rem}
.warning{background:#ffe8e8;border-left:5px solid #b42318;padding:1rem;border-radius:.3rem}
</style>""", unsafe_allow_html=True)


def badge():
    st.markdown('<span class="sim-badge">ข้อมูลจำลอง / SIMULATED DATA</span>', unsafe_allow_html=True)


def warning():
    st.markdown(f'<div class="warning"><b>คำเตือนสำคัญ</b><br>{DISCLAIMER_TH}</div>', unsafe_allow_html=True)


def show_metrics(metrics: pd.DataFrame) -> None:
    """Render compact metrics without Arrow conversion after native ML calls."""
    display = metrics.copy()
    for column in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]:
        display[column] = display[column].map(lambda value: f"{float(value):.3f}")
    st.markdown(display.to_html(index=False, classes="metrics-table"), unsafe_allow_html=True)


def show_table(frame: pd.DataFrame, max_rows: int = 30, include_index: bool = False) -> None:
    """Render report tables without relying on PyArrow's native conversion path."""
    visible = frame.head(max_rows).copy()
    numeric = visible.select_dtypes(include="number").columns
    visible[numeric] = visible[numeric].round(6)
    html = visible.to_html(index=include_index, classes="data-table", border=0, escape=True)
    st.markdown(f'<div style="overflow:auto;max-height:620px">{html}</div>', unsafe_allow_html=True)
    if len(frame) > max_rows:
        st.caption(f"แสดง {max_rows} จาก {len(frame)} แถว")


def run_demo():
    progress = st.progress(0, text="กำลังสร้างข้อมูลจำลอง")
    raw = generate_synthetic_data(); progress.progress(20, text="กำลังตรวจสอบข้อมูล")
    result = validate_dataframe(raw)
    if not result.valid: raise RuntimeError("; ".join(result.errors))
    raw.to_csv(RAW_DIR / "simulated_sparameters.csv", index=False)
    processed, operations = preprocess_data(raw)
    processed.to_csv(PROCESSED_DIR / "simulated_sparameters_processed.csv", index=False)
    progress.progress(45, text="กำลังสกัดคุณลักษณะ")
    features = extract_features(processed); features.to_csv(FEATURE_DIR / "simulated_features.csv", index=False)
    progress.progress(65, text="กำลังฝึก Machine Learning")
    ml = train_and_evaluate(features)
    progress.progress(90, text="กำลังสร้างกราฟ")
    figs = {"example_s11_s21.png": plot_measurement(raw, raw.measurement_id.iloc[0]),
            "average_signals_by_class.png": plot_average_by_class(raw),
            "class_distribution.png": plot_class_distribution(features),
            "model_metric_comparison.png": plot_metric_comparison(ml["metrics"])}
    for name, fig in figs.items(): fig.savefig(FIGURE_DIR / name, dpi=180, bbox_inches="tight"); plt.close(fig)
    # Models are persisted with Joblib; keeping native estimators out of session state
    # makes reruns and multiple browser sessions more robust.
    ml_session = {key: value for key, value in ml.items() if key != "models"}
    st.session_state.update(raw=raw, processed=processed, operations=operations, features=features, ml=ml_session)
    progress.progress(100, text="สำเร็จ"); st.success("สร้างและประมวลผลข้อมูลจำลองครบทั้ง pipeline แล้ว")


def get_data():
    if "raw" in st.session_state: return st.session_state.raw
    path = RAW_DIR / "simulated_sparameters.csv"
    if path.exists():
        st.session_state.raw = pd.read_csv(path); return st.session_state.raw
    return None


st.title("BoneWave")
st.caption("ระบบเพื่อสุขภาพสำหรับประเมินกลุ่มความเสี่ยงเบื้องต้นด้วยสัญญาณไมโครเวฟและ AI — งานวิจัยต้นแบบ")
warning()
pages = ["ภาพรวมระบบ", "สร้างข้อมูลจำลอง", "นำเข้าและตรวจสอบข้อมูล", "กราฟ S11 และ S21",
         "การเตรียมข้อมูล", "การสกัดคุณลักษณะ", "ฝึกและประเมินโมเดล", "ทดลองจำแนกตัวอย่าง",
         "ส่งออกผลลัพธ์", "ข้อจำกัดและคำชี้แจง"]
page = st.sidebar.radio("เมนู", pages)
st.sidebar.caption("สัญญาณและผลโมเดลทั้งหมดในรุ่นนี้เป็นข้อมูลจำลอง")

if page == "ภาพรวมระบบ":
    badge(); st.header("ภาพรวมระบบวิจัยต้นแบบ")
    st.write("BoneWave สาธิต pipeline ตั้งแต่สร้าง/นำเข้า S11 และ S21, ตรวจสอบ, เตรียมข้อมูล, สกัดคุณลักษณะ, ฝึกโมเดลแบบ group-aware และส่งออกหลักฐาน")
    if st.button("สร้างข้อมูลจำลองและประมวลผลตัวอย่างทั้งหมด", type="primary", width="stretch"):
        try: run_demo()
        except Exception as exc: st.exception(exc)
    if "ml" in st.session_state:
        st.subheader("ผลเปรียบเทียบล่าสุด (synthetic software-demo metrics)")
        show_metrics(st.session_state.ml["metrics"])
        pred = st.session_state.ml["predictions"].iloc[0]
        st.info(f"ตัวอย่าง: {pred.measurement_id} → {THAI_LABELS[pred.predicted_label]} (ป้ายกลุ่มทดลอง ไม่ใช่การวินิจฉัย)")

elif page == "สร้างข้อมูลจำลอง":
    badge(); st.header("สร้างข้อมูลจำลอง")
    c1, c2 = st.columns(2)
    samples = c1.number_input("จำนวน sample ต่อ class", 10, 50, 10)
    repeats = c2.number_input("จำนวน repeated measurements", 3, 10, 3)
    if st.button("สร้างข้อมูลด้วย random seed 42", type="primary"):
        raw = generate_synthetic_data(int(samples), int(repeats)); raw.to_csv(RAW_DIR / "simulated_sparameters.csv", index=False)
        st.session_state.raw = raw; st.success(f"สร้าง {raw.measurement_id.nunique()} measurements / {raw.sample_id.nunique()} samples")
        show_table(raw, max_rows=20)

elif page == "นำเข้าและตรวจสอบข้อมูล":
    badge(); st.header("นำเข้าและตรวจสอบ CSV")
    uploads = st.file_uploader("เลือกไฟล์ CSV หนึ่งไฟล์หรือหลายไฟล์", type="csv", accept_multiple_files=True)
    if uploads:
        valid_frames = []
        for upload in uploads:
            df, result = read_and_validate_csv(upload)
            if result.valid: st.success(f"{upload.name}: ผ่านการตรวจสอบ"); valid_frames.append(df)
            else:
                for error in result.errors: st.error(f"{upload.name}: {error}")
            for item in result.warnings: st.warning(f"{upload.name}: {item}")
        if valid_frames:
            combined = pd.concat(valid_frames, ignore_index=True); st.session_state.raw = combined
            show_table(combined, max_rows=30)

elif page == "กราฟ S11 และ S21":
    badge(); st.header("กราฟสัญญาณจำลอง S11 และ S21"); raw = get_data()
    if raw is None: st.info("กรุณาสร้างหรือนำเข้าข้อมูลก่อน")
    else:
        mid = st.selectbox("Measurement", raw.measurement_id.unique())
        fig = plot_measurement(raw, mid); st.pyplot(fig)
        st.download_button("ดาวน์โหลด PNG", figure_to_png(fig), "s11_s21_simulated.png", "image/png")
        avg = plot_average_by_class(raw); st.pyplot(avg)

elif page == "การเตรียมข้อมูล":
    badge(); st.header("การเตรียมข้อมูล"); raw = get_data()
    if raw is None: st.info("กรุณาสร้างหรือนำเข้าข้อมูลก่อน")
    else:
        interpolate = st.checkbox("Interpolate ช่องว่างขนาดเล็ก", value=False)
        smooth = st.checkbox("ใช้ Savitzky–Golay smoothing", value=False)
        if smooth: st.warning("เลือกใช้ smoothing: window=11, polyorder=2")
        if st.button("ประมวลผล"):
            try:
                processed, operations = preprocess_data(raw, interpolate, smooth)
                processed.to_csv(PROCESSED_DIR / "simulated_sparameters_processed.csv", index=False)
                st.session_state.update(processed=processed, operations=operations)
                st.success("สำเร็จ"); st.write(operations); show_table(processed, max_rows=10)
            except Exception as exc: st.error(str(exc))

elif page == "การสกัดคุณลักษณะ":
    badge(); st.header("การสกัดคุณลักษณะ")
    source = st.session_state.get("processed", get_data())
    if source is None: st.info("กรุณาเตรียมข้อมูลก่อน")
    elif st.button("สกัดคุณลักษณะ"):
        features = extract_features(source); features.to_csv(FEATURE_DIR / "simulated_features.csv", index=False)
        st.session_state.features = features; st.success(f"ได้ {features.shape[1]-4} features ต่อ measurement")
        show_table(features, max_rows=30)

elif page == "ฝึกและประเมินโมเดล":
    badge(); st.header("ฝึกและประเมิน Machine Learning")
    features = st.session_state.get("features")
    if features is None and (FEATURE_DIR / "simulated_features.csv").exists(): features = pd.read_csv(FEATURE_DIR / "simulated_features.csv")
    if features is None: st.info("กรุณาสกัดคุณลักษณะก่อน")
    elif st.button("ฝึกทั้ง 3 โมเดล", type="primary"):
        try:
            ml = train_and_evaluate(features); st.session_state.ml = {key: value for key, value in ml.items() if key != "models"}; st.success("ฝึกโมเดลสำเร็จ; sample overlap = 0")
            st.json(ml["metadata"]); show_metrics(ml["metrics"])
            fig = plot_metric_comparison(ml["metrics"]); st.pyplot(fig)
            for name in ml["models"]:
                path = RESULT_DIR / f"confusion_matrix_{name.lower()}.png"
                if path.exists(): st.image(str(path), caption=f"{name}: simulated confusion matrix")
        except Exception as exc: st.exception(exc)

elif page == "ทดลองจำแนกตัวอย่าง":
    badge(); st.header("ทดลองจำแนกตัวอย่าง"); warning()
    raw, features = get_data(), st.session_state.get("features")
    if features is None and (FEATURE_DIR / "simulated_features.csv").exists(): features = pd.read_csv(FEATURE_DIR / "simulated_features.csv")
    if raw is None or features is None: st.info("กรุณารัน demo workflow ก่อน")
    else:
        mid = st.selectbox("เลือก measurement", features.measurement_id)
        model_name = st.selectbox("เลือกโมเดล", ["DecisionTree", "RandomForest", "SVM"])
        model = st.session_state.get("ml", {}).get("models", {}).get(model_name)
        if model is None:
            path = MODEL_DIR / f"{model_name.lower()}_simulated.joblib"
            if path.exists(): model = joblib.load(path)
        if model is None: st.info("กรุณาฝึกโมเดลก่อน")
        elif st.button("จำแนกกลุ่มตัวอย่าง"):
            row = features[features.measurement_id == mid].iloc[[0]]; names = [c for c in features if c not in ["sample_id","measurement_id","label","data_source"]]
            predicted = model.predict(row[names])[0]
            st.metric("Predicted synthetic group", THAI_LABELS[predicted])
            st.error("เป็นป้ายกลุ่มตัวอย่างทดลอง ไม่ใช่การวินิจฉัย และใช้แทนแพทย์หรือ X-ray ไม่ได้")
            if hasattr(model, "predict_proba"):
                show_table(pd.DataFrame({"class": model.classes_, "probability": model.predict_proba(row[names])[0]}), max_rows=10)
            st.pyplot(plot_measurement(raw, mid)); show_table(row.T.rename(columns={row.index[0]: "value"}), max_rows=40, include_index=True)

elif page == "ส่งออกผลลัพธ์":
    badge(); st.header("ส่งออกผลลัพธ์ (ทั้งหมดเป็นข้อมูลจำลอง)")
    exports = [(RAW_DIR / "simulated_sparameters.csv", "text/csv"), (PROCESSED_DIR / "simulated_sparameters_processed.csv", "text/csv"),
               (FEATURE_DIR / "simulated_features.csv", "text/csv"), (RESULT_DIR / "model_metrics.csv", "text/csv"),
               (RESULT_DIR / "classification_report.csv", "text/csv"), (RESULT_DIR / "predictions.csv", "text/csv"),
               (RESULT_DIR / "run_metadata.json", "application/json")]
    for path, mime in exports:
        if path.exists(): st.download_button(f"ดาวน์โหลด {path.name}", path.read_bytes(), path.name, mime, key=str(path))
    for path in sorted(RESULT_DIR.glob("confusion_matrix_*.png")):
        st.download_button(f"ดาวน์โหลด {path.name}", path.read_bytes(), path.name, "image/png", key=str(path))
    for path in sorted(FIGURE_DIR.glob("*.png")):
        st.download_button(f"ดาวน์โหลด {path.name}", path.read_bytes(), path.name, "image/png", key=str(path))
    for path in sorted(MODEL_DIR.glob("*.joblib")):
        st.download_button(f"ดาวน์โหลด {path.name}", path.read_bytes(), path.name, "application/octet-stream", key=str(path))

else:
    badge(); st.header("ข้อจำกัดและคำชี้แจง"); warning()
    st.markdown("""- สัญญาณเป็นแบบจำลองเพื่อทดสอบซอฟต์แวร์ ไม่ใช่ electromagnetic หรือ biological simulation ที่ผ่านการยืนยัน
- ไม่มีข้อมูลผู้ป่วย การทดลองจริง ผลคลินิก หรือการวัดจาก NanoVNA
- Accuracy และ F1-score ที่แสดงเป็นผลบน synthetic dataset เท่านั้น ห้ามตีความเป็น medical accuracy
- ต้องมีการวิจัย เครื่องมืออ้างอิง จริยธรรม และการตรวจสอบโดยผู้เชี่ยวชาญก่อนใช้งานกับมนุษย์""")
