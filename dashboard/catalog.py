"""Danh mục trang: một nguồn cho cả bản Streamlit (views/) lẫn API (api/).

Mỗi trang: tiêu đề, icon (tên Material Symbols), đường dẫn, câu hỏi trang trả lời,
các bảng trang đọc, điều kiện tối thiểu để vẽ (`requires`) và các bộ lọc trang dùng.
"""
from data_layer import schema

_PAGES = [
    dict(
        title="Tổng quan", icon=":material/space_dashboard:", path="tong-quan",
        question="Chất lượng gán nhãn đang ở đâu, và hai KPI của đề (lỗi lặp lại, thời gian xử lý) là bao nhiêu?",
        tables=["issues", "workload"], requires={"issues": [], "workload": []},
        filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Top lỗi", icon=":material/leaderboard:", path="top-loi",
        question="Loại lỗi nào xuất hiện nhiều nhất, và loại nào cứ lặp lại?",
        tables=["issues"], requires={"issues": []}, filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Class khó", icon=":material/category:", path="class-kho",
        question="Class nào khó gán nhất, và mỗi class hay dính loại lỗi nào?",
        tables=["issues", "workload"], requires={"issues": [], "workload": []},
        filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Annotator", icon=":material/group:", path="annotator",
        question="Annotator nào cần hỗ trợ, và cần hỗ trợ về loại lỗi gì?",
        tables=["issues", "workload", "annotators"], requires={"issues": [], "workload": []},
        filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Annotator chấm annotator", icon=":material/compare_arrows:", path="cham-cheo-annotator",
        question="Không có đáp án thì ai lệch khỏi nhóm, và vật nào khiến các annotator bất đồng?",
        tables=["pair_agreement", "object_votes", "gt_scores", "image_scores"],
        requires={"pair_agreement": []}, filters={"class", "size", "annotator"},
    ),
    dict(
        title="Reviewer chấm annotator", icon=":material/rate_review:", path="cham-cheo-reviewer",
        question="Issue nhiều là do annotator yếu hay do reviewer khó?",
        tables=["issues", "workload", "review_assignments", "reviewer_overlap", "reviewers"],
        requires={"issues": [], "workload": []}, filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Reviewer yêu cầu vs annotator sửa", icon=":material/build:", path="sua-annotator",
        question="Sau khi reviewer yêu cầu sửa, annotator có sửa đúng điều được yêu cầu không?",
        tables=["issues"],
        requires={"issues": ["requested_action", "fix_arm", "fix_outcome", "observed_change"]},
        filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Agent đề xuất vs người áp dụng", icon=":material/smart_toy:", path="sua-agent",
        question="Đề xuất sửa của agent có đúng không, và người duyệt có lọc được đề xuất sai?",
        tables=["patches", "issues"], requires={"patches": []}, filters={"run", "class", "annotator"},
    ),
    dict(
        title="Khuyến nghị vs kết quả pilot", icon=":material/science:", path="khuyen-nghi-pilot",
        question="Khuyến nghị nào đã được áp dụng, và lỗi của cụm đó có giảm sau pilot không?",
        tables=["recommendations"], requires={"recommendations": []}, filters={"class"},
    ),
    dict(
        title="Chi tiết issue", icon=":material/pageview:", path="chi-tiet-issue",
        question="Một issue cụ thể trông thế nào: ảnh, comment, loại lỗi, nguồn được quy và cách nó được xử lý?",
        tables=["issues", "patches"], requires={"issues": []}, filters={"run", "class", "size", "annotator"},
    ),
    dict(
        title="Nguồn dữ liệu", icon=":material/database:", path="nguon-du-lieu",
        question="Dashboard đang chạy trên bảng nào, bảng nào còn thiếu, và pipeline cần nộp những cột gì?",
        tables=list(schema.TABLES), filters=set(),
    ),
]

PAGES = {page["path"]: page for page in _PAGES}

SECTIONS = {
    "Theo đề M22": ["tong-quan", "top-loi", "class-kho", "annotator"],
    "Chấm chéo": ["cham-cheo-annotator", "cham-cheo-reviewer"],
    "Đề xuất vs sửa": ["sua-annotator", "sua-agent", "khuyen-nghi-pilot"],
    "Tra cứu": ["chi-tiet-issue", "nguon-du-lieu"],
}
