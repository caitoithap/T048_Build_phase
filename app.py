import os
import sys
import site
import ctypes

# Fix Windows DLL WinError 1114 (Explicit C++ DLL Preloading for PyTorch on Windows)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

if sys.platform == "win32":
    site_dirs = site.getsitepackages() + [site.getusersitepackages()]
    for sp in site_dirs:
        t_lib = os.path.join(sp, "torch", "lib")
        if os.path.exists(t_lib):
            try:
                os.add_dll_directory(t_lib)
                for dll_name in ["libiomp5md.dll", "c10.dll", "torch_cpu.dll", "torch_python.dll"]:
                    dll_p = os.path.join(t_lib, dll_name)
                    if os.path.exists(dll_p):
                        try:
                            ctypes.CDLL(dll_p)
                        except Exception:
                            pass
            except Exception:
                pass

from pathlib import Path
import time
import cv2
import pandas as pd
import numpy as np
import streamlit as st

# Add current directory to path
sys.path.append(str(Path(__file__).resolve().parent))

import config
from src.qc_rules import QCRuleEngine
from src.model_assisted_qc import ModelAssistedQCAuditor
from src.qc_agent import QCAuditorAgent
from src.report_generator import QCReportExporter
from src.cvat_api import CVATApiClient
from src.analytics_mart import QualityAnalyticsMart

st.set_page_config(
    page_title="CVAT Automated QC & AI Reviewer Agent System",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 CVAT Automated QC & AI Reviewer Agent System")
st.markdown("**Hệ Thống Kiểm Định Chất Lượng Nhãn & Reviewer Agent AI (Sơ đồ Kiến Trúc CVAT - Stitch)** | *VinUni AI20K*")

# Sidebar Configuration
st.sidebar.header("⚙️ Data Ingestion & QC Settings")

ingestion_mode = st.sidebar.radio(
    "CHỌN NGUỒN NẠP DỮ LIỆU (INGESTION MODE):",
    ["🌐 CVAT REST API / Live Server Mode", "📁 Local File Upload Mode (.XML / .JSON)"],
    index=0
)

st.sidebar.divider()
st.sidebar.subheader("🔍 Rule-Based & AI Thresholds")
min_box_size = st.sidebar.slider("Min Bbox Size (px)", 5, 50, int(config.MIN_BBOX_SIZE_PX), 5)
dup_iou_thresh = st.sidebar.slider("Duplicate IoU Threshold", 0.5, 0.95, config.DUPLICATE_IOU_THRESH, 0.05)
model_conf = st.sidebar.slider("AI Audit Confidence", 0.50, 0.90, config.MODEL_ASSIST_CONF, 0.05)

st.sidebar.subheader("🤖 Gemini API Key (AI Agent)")
gemini_key_input = st.sidebar.text_input("Gemini API Key (Optional)", value=config.GEMINI_API_KEY, type="password")

# Main Tabs matching diagram
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Run Ingestion & Audit", 
    "📈 Quality Analytics Mart & Dashboard", 
    "🤖 AI QA Agent Co-Pilot", 
    "📊 Visual Image Error Inspection", 
    "🛠️ Human Action & Feedback Loop"
])

with tab1:
    st.subheader("1. Cấu Hình Nguồn Dữ Liệu Đầu Vào (Data Ingestion Layer)")
    annotator_name = st.text_input("Họ tên Học viên / Annotator:", "Nguyễn Trọng Hùng")

    xml_input_path = "output/pre_annotations_cvat.xml"
    img_folder_input = "sample_data"
    cvat_issues_data = []

    if "CVAT REST API" in ingestion_mode:
        st.info("🔗 **Chế độ Live CVAT REST API Sync:** Chọc trực tiếp vào CVAT Server qua API / Webhook")
        c1, c2, c3 = st.columns([2, 1, 1])
        cvat_url = c1.text_input("CVAT Server URL:", "https://app.cvat.ai")
        task_id = c2.text_input("CVAT Task ID / Job ID:", "108361")
        use_mock = c3.checkbox("Simulate / Mock API Mode", value=True, help="Dùng chế độ mô phỏng khi CVAT Server offline")

        if use_mock:
            st.warning("⚡ Đang bật chế độ **Simulate API Ingestion**: Tự động tải Task metadata, annotations XML và Reviewer Issues từ CVAT API MOCK.")
            cvat_client = CVATApiClient(server_url=cvat_url)
            task_meta, xml_input_path, cvat_issues_data = cvat_client.mock_fetch_task_data(task_id, xml_input_path, "output")
            st.json({"CVAT Task Ingested": task_meta})
        else:
            auth_token = st.text_input("CVAT API Token (Optional):", type="password")
            if st.button("🔗 Test Connection to CVAT"):
                client = CVATApiClient(server_url=cvat_url, auth_token=auth_token)
                ok, msg = client.test_connection()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
    else:
        st.info("📁 **Chế độ Offline Local File:** Up file XML (CVAT 1.1) hoặc COCO JSON thủ công")
        col_input1, col_input2 = st.columns(2)
        with col_input1:
            xml_file_upload = st.file_uploader("Tải file XML / JSON:", type=["xml", "json"])
            if xml_file_upload:
                saved_xml = Path("output/uploaded_audit.xml")
                saved_xml.parent.mkdir(parents=True, exist_ok=True)
                with open(saved_xml, "wb") as f:
                    f.write(xml_file_upload.getbuffer())
                xml_input_path = str(saved_xml)
                st.success("✅ Đã nạp file nhãn!")

        with col_input2:
            img_folder_input = st.text_input("Thư mục chứa ảnh:", "sample_data")

    st.divider()
    audit_btn = st.button("🚀 Bắt đầu Kiểm Định QC Tự Động & Chạy AI QA Agent", type="primary")

    if audit_btn:
        if not Path(xml_input_path).exists():
            st.error(f"❌ File nhãn [{xml_input_path}] không tồn tại!")
        elif not Path(img_folder_input).exists():
            st.error(f"❌ Thư mục ảnh [{img_folder_input}] không tồn tại!")
        else:
            st.info("⚡ Đang thực thi luồng Data Standardization -> AI Issue Understanding -> Quality Analytics Engine...")
            prog = st.progress(10)

            # Step 1: Rule-based QC
            rule_engine = QCRuleEngine(min_size=min_box_size, dup_iou=dup_iou_thresh)
            parsed_anns = rule_engine.parse_cvat_xml(xml_input_path)
            passed_anns, rule_errors, rule_stats = rule_engine.audit_annotations(parsed_anns)
            prog.progress(40)

            # Step 2: Model-assisted Audit
            model_auditor = ModelAssistedQCAuditor(conf_thresh=model_conf)
            missing_objs, class_mismatches = model_auditor.audit_missing_and_mislabels(img_folder_input, parsed_anns)
            prog.progress(65)

            # Step 3: Quality Analytics Mart computation
            analytics_mart = QualityAnalyticsMart.compute_analytics_mart(
                rule_errors, missing_objs, class_mismatches, rule_stats["total_audited_annotations"], annotator_name=annotator_name
            )
            prog.progress(80)

            # Step 4: AI QA Agent Evaluation
            agent = QCAuditorAgent(api_key=gemini_key_input)
            agent_report = agent.evaluate_audit_results(
                rule_stats, rule_errors, missing_objs, class_mismatches, analytics_mart, cvat_issues_data, annotator_name=annotator_name
            )
            prog.progress(95)

            # Step 5: Export HTML Report
            report_html_p = "output/qc_audit_report.html"
            QCReportExporter.export_html_report(agent_report, rule_stats, rule_errors, missing_objs, class_mismatches, report_html_p)
            prog.progress(100)

            st.session_state["agent_report"] = agent_report
            st.session_state["rule_stats"] = rule_stats
            st.session_state["rule_errors"] = rule_errors
            st.session_state["missing_objs"] = missing_objs
            st.session_state["class_mismatches"] = class_mismatches
            st.session_state["analytics_mart"] = analytics_mart
            st.session_state["cvat_issues_data"] = cvat_issues_data
            st.session_state["report_html_p"] = report_html_p
            st.session_state["audit_img_folder"] = img_folder_input

            st.success("🎉 Hoàn tất kiểm định QC và tính toán Analytics Mart thành công!")

with tab2:
    st.subheader("📈 Quality Analytics Mart & Executive Dashboard (Stitch UI)")
    if "analytics_mart" in st.session_state:
        mart = st.session_state["analytics_mart"]
        rep = st.session_state["agent_report"]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng Số Nhãn Audited", mart["total_audited"])
        m2.metric("Điểm Chất Lượng", f"{rep['quality_score']} / 100")
        m3.metric("Tỷ Lệ Lỗi (Issue Rate)", f"{mart['issue_rate']}%")
        m4.metric("Annotator Risk Tier", mart["annotator_risk"]["risk_badge"])

        st.divider()

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("### 🏆 Top Difficult Classes Matrix (Mức độ khó của Class)")
            df_classes = pd.DataFrame(mart["difficult_classes"])
            if not df_classes.empty:
                st.bar_chart(df_classes.set_index("class_name")["error_count"])
                st.table(df_classes)
            else:
                st.success("Không có Class nào bị lỗi!")

        with c_right:
            st.markdown("### 🔄 Recurring Issues & Error Trends")
            df_recurring = pd.DataFrame(mart["recurring_issues"])
            st.table(df_recurring)

            st.markdown("### 👤 Annotator Risk Profile & Coaching Need")
            st.info(f"**Annotator:** {mart['annotator_risk']['annotator_name']}\n\n"
                    f"**Mức độ rủi ro:** {mart['annotator_risk']['risk_level']}\n\n"
                    f"**Khuyến nghị:** {mart['annotator_risk']['recommendation']}")
    else:
        st.info("Vui lòng bấm nút '🚀 Bắt đầu Kiểm Định QC' tại Tab 1 để tạo Dashboard phân tích.")

with tab3:
    st.subheader("🤖 AI QA Agent Co-Pilot (Root Cause & Recommendation Engine)")
    if "agent_report" in st.session_state:
        rep = st.session_state["agent_report"]
        issues = st.session_state.get("cvat_issues_data", [])

        st.markdown(f"### Quyết định AI Agent: **{rep['decision_label']}**")
        st.markdown(f"#### 💡 Recommended Action Plan:\n`{rep['recommended_action']}`")

        st.divider()
        st.markdown("### 📝 Báo Cáo Nhận Xét Tự Động Từ AI QA Agent")
        st.markdown(rep["feedback_text"])

        if issues:
            st.divider()
            st.markdown("### 💬 Phản Hồi Từ CVAT Reviewers (Reviewer Issues & Comments)")
            st.table(pd.DataFrame(issues))
    else:
        st.info("Chưa có kết quả từ AI Agent. Vui lòng thực thi kiểm định tại Tab 1.")

with tab4:
    st.subheader("📊 Visual Image Error Inspection")
    if "rule_errors" in st.session_state:
        rule_errors = st.session_state["rule_errors"]
        missing_objs = st.session_state["missing_objs"]
        img_folder = st.session_state["audit_img_folder"]

        all_flagged = rule_errors + missing_objs
        if all_flagged:
            flagged_frames = sorted(list(set([e["frame_name"] for e in all_flagged])))
            sel_frame = st.selectbox("Chọn ảnh có lỗi để soi chi tiết:", flagged_frames)
            
            img_p = Path(img_folder) / sel_frame
            frame = cv2.imread(str(img_p))

            if frame is not None:
                frame_errs = [e for e in all_flagged if e["frame_name"] == sel_frame]

                for err in frame_errs:
                    x, y, w, h = [int(v) for v in err["bbox"]]
                    err_t = err["error_type"]
                    lbl = f"⚠️ {err_t}: {err.get('class_name', '')}"
                    
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(frame, lbl, (x, max(25, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption=f"Ảnh: {sel_frame} ({len(frame_errs)} lỗi)", use_column_width=True)
                st.write("### Chi tiết các lỗi trên ảnh này:")
                st.table(pd.DataFrame(frame_errs)[["error_type", "class_name", "bbox", "error_msg"]])
        else:
            st.success("🎉 Không phát hiện lỗi nào trên tập dữ liệu này!")
    else:
        st.info("Bấm chạy QC Audit ở Tab 1 để rà vết lỗi trên hình ảnh.")

with tab5:
    st.subheader("🛠️ Human Action & CVAT Rework Feedback Loop")
    if "agent_report" in st.session_state:
        rep = st.session_state["agent_report"]
        
        st.markdown("### 📋 1. Quy Trình Phản Hồi Sửa Nhãn (Human Action Workflow)")
        col_act1, col_act2, col_act3 = st.columns(3)
        col_act1.button("📩 Gửi Yêu Cầu Rework Sang CVAT", help="Push Ticket Rework lên Task CVAT")
        col_act2.button("📚 Gán Bài Đọc Guideline Cho Annotator", help="Gửi link quy chuẩn nhãn")
        col_act3.button("🎓 Mở Lớp Coaching 1-1 Với Mentor", help="Đặt lịch mentor đào tạo lại")

        st.divider()
        st.markdown("### 🔄 2. Tái Kiểm Định Chất Lượng (Measure Again)")
        st.caption("Sau khi Annotator sửa nhãn trên CVAT, bấm nút bên dưới để tải lại dữ liệu mới và tái đo lường chất lượng nhãn.")
        if st.button("🔄 Tái Kiểm Định Lại Bộ Nhãn (Measure Again Cycle)"):
            st.success("🔄 Đã kích hoạt vòng lặp Tái Kiểm Định (Re-Audit Loop)!")

        st.divider()
        st.markdown("### 💾 3. Xuất Báo Cáo QC (Export Audit Artifacts)")
        with open(st.session_state["report_html_p"], "rb") as f:
            st.download_button("💾 Tải Báo Cáo HTML QC Auditor Report", f, file_name="qc_audit_report.html", mime="text/html")
    else:
        st.info("Thực thi kiểm định tại Tab 1 để kích hoạt vòng lặp Human Action.")
