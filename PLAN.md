# KẾ HOẠCH CẢI THIỆN HỆ THỐNG M22 (BUILD PHASE)

Dự án: **CVAT Issue Analytics Dashboard & AI Reviewer Agent (M22)**  
Nhóm thực hiện: **T048**

---

## 📌 Tổng quan các bước thực hiện

| Bước | Nội dung công việc | Trạng thái | Tiêu chí hoàn thành | Lệnh kiểm tra |
| :---: | :--- | :---: | :--- | :--- |
| **1** | Sửa các lỗi tiềm ẩn và đồng bộ biến cấu hình trong `config.py`, `src/detector.py`, `src/qc_filter.py`, `cli.py` | ✅ **Hoàn thành** | Không còn lỗi `AttributeError` khi nạp config; `cli.py` tự fallback nạp annotation có sẵn nếu file mặc định chưa tạo. | `.venv/bin/python -c "import config; from src.detector import YOLOCPUDetector; from src.qc_filter import QCFilter; d = YOLOCPUDetector(); q = QCFilter()"` |
| **2** | Xây dựng bộ kiểm thử tự động toàn diện (`tests/`) cho QC rules, Data Layer, FastAPI API và CLI | ⏳ Chưa bắt đầu | Tạo 4 test suites: `test_qc_rules.py`, `test_data_layer.py`, `test_api_endpoints.py`, `test_cli.py`. Chạy pass 100%. | `.venv/bin/pytest tests/ -v` |
| **3** | Chuyển đổi toàn bộ 8 trang phân tích còn lại từ `dashboard/views/` sang `dashboard/api/pages/` (FastAPI Server-Driven UI) | ⏳ Chưa bắt đầu | 8 trang (`top_errors`, `classes`, `annotators`, `cross_annotators`, `cross_reviewers`, `fix_annotator`, `fix_agent`, `fix_recommendations`) được tạo và đăng ký vào `BUILDERS`. | `.venv/bin/python -m pytest tests/test_api_endpoints.py -v` |
| **4** | Đồng bộ Frontend React (`dashboard/web`) tương thích với các trang API mới (Icon & Router) | ⏳ Chưa bắt đầu | Bổ sung đầy đủ icons Material trong `web/src/lib/icons.tsx`; `/api/meta` trả về `ported: true` cho toàn bộ trang phân tích. | `.venv/bin/python -c "from dashboard.api.pages import PORTED, BUILDERS; import catalog; assert len(BUILDERS) >= 9"` |
| **5** | Đóng gói tài liệu, cập nhật REPORT.md, README.md và script khởi chạy tiện ích | ⏳ Chưa bắt đầu | `README.md` cập nhật hướng dẫn FastAPI + React; `REPORT.md` cập nhật tiến độ chặng mới; toàn bộ test pass. | `.venv/bin/pytest tests/ -v && git status` |

---

## 📝 Nhật ký tiến độ (Execution Progress)

- **Bước 1 (18/10/2026):**
  - Đã thêm các hằng số mặc định vào `config.py`: `DEFAULT_MODEL`, `DEFAULT_CONF_THRESHOLD`, `DEFAULT_MIN_BOX_SIZE`, `DEFAULT_MAX_BOX_ASPECT_RATIO`, `TARGET_CLASSES`.
  - Đã thêm cơ chế fallback tự động cho `cli.py`: nếu `output/pre_annotations_cvat.xml` chưa tồn tại, tự động nạp `sample_data_output1/annotations.xml`.
  - Đã kiểm tra khởi tạo `YOLOCPUDetector`, `QCFilter` và chạy lệnh `cli.py` thành công 100%.
