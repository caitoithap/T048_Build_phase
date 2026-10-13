"""Hợp đồng dữ liệu giữa pipeline và dashboard.

Mỗi bảng thật đặt vào thư mục bảng thật với tên `<tên bảng>.csv` hoặc `.parquet`.

- `columns`: mọi cột dashboard đọc, kèm ý nghĩa.
- `optional`: cột chưa cần có ngay, kèm chặng sinh ra nó. Cột không nằm ở đây là BẮT BUỘC.
  Bảng đủ cột bắt buộc là được nhận; phần giao diện nào cần cột còn thiếu thì ghi rõ còn chờ gì.
- `enums`: cột chỉ nhận các MÃ của một bộ mã trong settings.VOCAB. Giá trị lạ làm cả bảng bị từ chối.
- `bools`: cột đúng/sai. Nhận True/False, 1/0, "true"/"false" (SQLite lưu 1/0).

Cột gắn nhãn "cần đáp án" chỉ tính được khi có ground truth.
"""

C1 = "chặng C · ingest"
C2 = "chặng C · map vào annotation"
C3 = "chặng C · phân loại comment"
D = "chặng D · mart"
F = "chặng F · quy nguồn"
G = "chặng G · can thiệp"
H = "chặng H · pilot"
A3 = "chặng A · chạy annotator"
A4 = "chặng A · so khớp"
A6 = "chặng A · phân công reviewer"
GT = "cần đáp án"

_PX = "toạ độ box theo pixel ảnh gốc"


def _box(prefix: str, meaning: str) -> dict[str, str]:
    """Bốn cột toạ độ <prefix>x1, y1, x2, y2."""
    cols = [f"{prefix}{k}" for k in ("x1", "y1", "x2", "y2")]
    return {cols[0]: f"{meaning}, {_PX}", **{c: "" for c in cols[1:]}}


TABLES = {
    "issues": {
        "title": "Issue đã làm giàu",
        "stage": C1,
        "desc": "Mỗi dòng một issue của reviewer. Các chặng sau bổ sung dần cột vào chính bảng này.",
        "columns": {
            "issue_id": "Mã issue",
            "run": "Lần chạy",
            "job_id": "Mã job trên CVAT",
            "job_order": "Thứ tự job của annotator theo thời gian, bắt đầu từ 1",
            "annotator": "Annotator bị mở issue",
            "reviewer": "Người mở issue",
            "image": "Tên file ảnh",
            "class_name": "Class của vật mà issue nói tới",
            "error_type": "Loại lỗi (9 loại). Nhóm lỗi do dashboard tự suy ra",
            "size_bucket": "Cỡ của box hoặc của vùng issue",
            "created_at": "Thời điểm mở issue",
            "resolved": "Issue đã đóng",
            "comment": "Comment đầu tiên của reviewer",
            "reply": "Trả lời của annotator, nếu có",
            "is_second_review": "Issue đến từ lượt chấm thứ hai của cùng job",
            "class_pred": "Class annotator đã gán, trống nếu thiếu box",
            "source": "Nguồn gốc box: trường source của CVAT, hoặc none nếu issue báo thiếu vật",
            "requested_action": "Thao tác reviewer yêu cầu, trích từ comment",
            "resolved_at": "Thời điểm đóng issue",
            "resolution_hours": "Số giờ từ lúc mở đến lúc đóng. Thiếu thì dashboard tự tính từ hai mốc thời gian",
            "is_recurrent": "Cùng annotator đã có cùng loại lỗi ở một job trước đó",
            "attributed_source": "Nguồn lỗi được quy",
            "fix_arm": "Luồng xử lý issue",
            "observed_change": "Thay đổi thực tế trên annotation sau khi đóng issue",
            "fix_outcome": "Kết quả của luồng annotator tự sửa",
            "object_id": "Mã vật trong đáp án, -1 nếu không ứng với vật nào",
            "is_false_alarm": "Reviewer báo nhầm, annotation vốn đúng",
            "still_wrong": "Sau khi xử lý annotation vẫn sai",
            **_box("i", "Vùng reviewer đánh dấu issue (trường position của CVAT)"),
            **_box("s", "Box annotator đã nộp"),
            **_box("g", "Box đáp án"),
        },
        "optional": {
            "reply": C1, "resolved_at": C1, **{c: C1 for c in _box("i", "")},
            "is_second_review": A6,
            "class_pred": C2, "source": C2, **{c: C2 for c in _box("s", "")},
            "requested_action": C3,
            "resolution_hours": D, "is_recurrent": D,
            "attributed_source": F,
            "fix_arm": G, "observed_change": G, "fix_outcome": G,
            "object_id": GT, "is_false_alarm": GT, "still_wrong": GT, **{c: GT for c in _box("g", "")},
        },
        "enums": {
            "run": "run", "class_name": "class", "class_pred": "class", "error_type": "error_type",
            "size_bucket": "size", "source": "box_source", "attributed_source": "attributed",
            "requested_action": "action", "fix_arm": "fix_arm", "observed_change": "change",
            "fix_outcome": "fix_outcome",
        },
        "bools": ["resolved", "is_second_review", "is_recurrent", "is_false_alarm", "still_wrong"],
    },
    "workload": {
        "title": "Khối lượng đã review",
        "stage": D,
        "desc": "Mẫu số của mọi tỷ lệ: số vật đã review theo job, reviewer, class, cỡ box.",
        "columns": {
            "run": "Lần chạy", "job_id": "Mã job", "job_order": "Thứ tự job",
            "annotator": "Annotator", "reviewer": "Reviewer",
            "class_name": "Class", "size_bucket": "Cỡ box",
            "n_reviewed": "Số annotation đã review cộng số vật bị báo thiếu",
        },
        "enums": {"run": "run", "class_name": "class", "size_bucket": "size"},
    },
    "review_assignments": {
        "title": "Phân công reviewer",
        "stage": A6,
        "desc": "Ai chấm job nào, kể cả job không có issue. CVAT không lưu lịch sử này.",
        "columns": {
            "run": "Lần chạy", "job_id": "Mã job", "job_order": "Thứ tự job",
            "annotator": "Annotator", "reviewer": "Reviewer",
            "n_annotations": "Số annotation trong các frame đã xem", "n_issues": "Số issue đã mở",
            "is_second_review": "Lượt chấm thứ hai của cùng job", "n_frames": "Số frame đã xem",
            "n_true_errors": "Số lỗi thật trong các frame đó", "n_false_alarms": "Số issue báo nhầm",
        },
        "optional": {"is_second_review": A6, "n_frames": A6, "n_true_errors": GT, "n_false_alarms": GT},
        "enums": {"run": "run"},
        "bools": ["is_second_review"],
    },
    "reviewer_overlap": {
        "title": "Hai reviewer cùng chấm một job",
        "stage": D,
        "desc": "Mức trùng nhau giữa hai reviewer trên cùng job.",
        "columns": {
            "run": "Lần chạy", "job_id": "Mã job", "annotator": "Annotator",
            "reviewer_a": "Reviewer thứ nhất", "reviewer_b": "Reviewer thứ hai",
            "n_both": "Số vật cả hai cùng báo", "n_only_a": "Chỉ người thứ nhất báo",
            "n_only_b": "Chỉ người thứ hai báo",
        },
        "enums": {"run": "run"},
    },
    "pair_agreement": {
        "title": "Đồng thuận từng cặp annotator",
        "stage": A4,
        "desc": "Kết quả so nhãn của annotator A với annotator B trên cùng ảnh, có đủ hai chiều.",
        "columns": {
            "annotator_a": "Annotator thứ nhất", "annotator_b": "Annotator thứ hai",
            "class_name": "Class", "size_bucket": "Cỡ box",
            "n_same": "Cả hai vẽ, cùng class, box khớp",
            "n_class_diff": "Cả hai vẽ nhưng khác class",
            "n_box_off": "Cùng class nhưng box lệch nhau",
            "n_only_a": "Chỉ annotator thứ nhất vẽ", "n_only_b": "Chỉ annotator thứ hai vẽ",
        },
        "enums": {"class_name": "class", "size_bucket": "size"},
    },
    "object_votes": {
        "title": "Số phiếu của từng vật",
        "stage": A4,
        "desc": "Mỗi dòng một vật: bao nhiêu annotator cùng vẽ nó.",
        "columns": {
            "object_key": "Mã vật", "image": "Tên file ảnh", "class_name": "Class",
            "size_bucket": "Cỡ box", "n_votes": "Số annotator vẽ vật này",
            "in_gt": "Vật có trong đáp án",
        },
        "optional": {"in_gt": GT},
        "enums": {"class_name": "class", "size_bucket": "size"},
        "bools": ["in_gt"],
    },
    "gt_scores": {
        "title": "Điểm theo đáp án",
        "stage": f"{A4}, {GT}",
        "desc": "Số đếm để tính precision, recall, F1 của từng annotator. Cả bảng cần đáp án.",
        "columns": {
            "annotator": "Annotator", "class_name": "Class", "size_bucket": "Cỡ box",
            "n_objects": "Số vật trong đáp án", "n_drawn": "Số box annotator nộp",
            "n_correct": "Số box đúng cả vị trí lẫn class",
        },
        "enums": {"class_name": "class", "size_bucket": "size"},
    },
    "image_scores": {
        "title": "Điểm theo ảnh",
        "stage": A4,
        "desc": "Mức đồng thuận giữa các annotator và tỷ lệ lỗi thật trên từng ảnh.",
        "columns": {
            "image": "Tên file ảnh", "n_objects": "Số vật trên ảnh",
            "agreement": "Đồng thuận trung bình giữa các cặp annotator trên ảnh",
            "error_rate": "Tỷ lệ lỗi trung bình của các annotator trên ảnh",
        },
        "optional": {"error_rate": GT},
    },
    "patches": {
        "title": "Bản vá của agent",
        "stage": G,
        "desc": "Mỗi dòng một issue đi qua luồng agent: đề xuất, quyết định của người, kết quả ghi.",
        "columns": {
            "patch_id": "Mã bản vá", "issue_id": "Issue tương ứng", "run": "Lần chạy",
            "annotator": "Annotator", "class_name": "Class",
            "operation": "Thao tác agent định làm",
            "mapped": "Issue map được vào annotation", "proposed": "Agent đưa ra được đề xuất",
            "decision": "Trạng thái của đề xuất, gồm cả quyết định của người duyệt",
            "applied": "Đã ghi vào CVAT", "issue_closed": "Reviewer đã đóng issue",
            "error_group": "Nhóm lỗi của issue",
            "iou_proposed_final": "IoU giữa box đề xuất và box được áp dụng",
            "minutes_to_decide": "Số phút người duyệt bỏ ra",
            "proposed_class": "Class agent đề xuất", "final_class": "Class sau khi áp dụng",
            **_box("p", "Box agent đề xuất"), **_box("f", "Box sau khi áp dụng"),
            "is_false_alarm": "Issue gốc là báo nhầm",
            "proposal_correct": "Đề xuất khớp đáp án",
            "final_correct": "Annotation sau cùng đúng",
        },
        "optional": {
            "error_group": C3, "iou_proposed_final": G, "minutes_to_decide": G,
            "proposed_class": G, "final_class": G, **{c: G for c in _box("p", "")}, **{c: G for c in _box("f", "")},
            "is_false_alarm": GT, "proposal_correct": GT, "final_correct": GT,
        },
        "enums": {"run": "run", "class_name": "class", "operation": "action", "decision": "decision",
                  "error_group": "error_group", "proposed_class": "class", "final_class": "class"},
        "bools": ["mapped", "proposed", "applied", "issue_closed", "is_false_alarm", "proposal_correct",
                  "final_correct"],
    },
    "recommendations": {
        "title": "Khuyến nghị và kết quả pilot",
        "stage": F,
        "desc": "Mỗi dòng một khuyến nghị ở mức quy trình. Chặng pilot bổ sung tỷ lệ lỗi trước và sau.",
        "columns": {
            "rec_id": "Mã khuyến nghị", "scope": "Đối tượng: mã annotator hoặc mã reviewer",
            "error_group": "Nhóm lỗi được nhắm tới", "class_name": "Class",
            "attributed_source": "Nguồn lỗi được quy", "action": "Hành động đề xuất (văn bản tự do)",
            "status": "Trạng thái của khuyến nghị",
            "measurable": "Đo được bằng pilot hay chỉ sinh tài liệu",
            "n_control": "Số issue của cụm ở lần đối chứng",
            "rate_control": "Issue trên 100 vật đã review, lần đối chứng",
            "rate_pilot": "Issue trên 100 vật đã review, lần pilot",
            "side_group": "Nhóm lỗi có thể tăng do tác dụng phụ",
            "side_rate_control": "Tỷ lệ lỗi phụ, lần đối chứng",
            "side_rate_pilot": "Tỷ lệ lỗi phụ, lần pilot",
        },
        "optional": {"n_control": H, "rate_control": H, "rate_pilot": H, "side_group": H,
                     "side_rate_control": H, "side_rate_pilot": H},
        "enums": {"error_group": "error_group", "class_name": "class", "attributed_source": "attributed",
                  "status": "rec_status", "side_group": "error_group"},
        "bools": ["measurable"],
    },
    "annotators": {
        "title": "Danh sách annotator",
        "stage": A3,
        "desc": "Model, họ model và cấu hình của từng annotator.",
        "columns": {
            "annotator": "Mã annotator", "model": "Model gốc",
            "family": "Họ model (các model cùng họ thường sai giống nhau)",
            "config": "Cấu hình và chính sách sửa",
        },
        "optional": {"model": A3, "family": A3, "config": A3},
    },
    "reviewers": {
        "title": "Danh sách reviewer",
        "stage": A6,
        "desc": "Phong cách chấm của từng reviewer.",
        "columns": {"reviewer": "Mã reviewer", "style": "Phong cách chấm"},
        "optional": {"style": A6},
    },
}


def required(name: str) -> list[str]:
    spec = TABLES[name]
    return [c for c in spec["columns"] if c not in spec.get("optional", {})]
