"""Chi tiết issue: ảnh có box, comment, phân loại và trạng thái xử lý."""
import pandas as pd
import streamlit as st

import settings as S
from data_layer import store
from ui import images, theme
from ui import components as ui

META = dict(
    title="Chi tiết issue", icon=":material/pageview:", path="chi-tiet-issue",
    question="Một issue cụ thể trông thế nào: ảnh, comment, loại lỗi, nguồn được quy và cách nó được xử lý?",
    tables=["issues", "patches"], requires={"issues": []}, filters={"run", "class", "size", "annotator"},
)
ALL = "Tất cả"
MAX_LISTED = 500
ROW_PX = 35  # chiều cao một dòng của bảng, để bảng thông tin hiện đủ không phải cuộn
# Các dòng chỉ hiện khi bảng issues đã có cột tương ứng.
LATER_FACTS = [("source", "Nguồn gốc box"), ("attributed_source", "Nguồn lỗi được quy"),
               ("requested_action", "Reviewer yêu cầu"), ("fix_arm", "Luồng xử lý")]


def _facts(issue: pd.Series, data: store.Tables) -> pd.DataFrame:
    annotator = issue["annotator"] + (f" ({issue['model']})" if pd.notna(issue["model"]) else "")
    rows = [("Annotator", annotator), ("Reviewer", issue["reviewer"]),
            ("Job", f"{issue['job_id']} · {issue['run']}"), ("Class", issue["class_name"]),
            ("Loại lỗi", issue["error_type"])]
    if data.has("issues", "is_recurrent"):
        rows.append(("Lặp lại", "Có" if issue["is_recurrent"] else "Không"))
    rows += [(label, issue[col]) for col, label in LATER_FACTS if data.has("issues", col) and pd.notna(issue[col])]
    status = "Đã đóng" if issue["resolved"] else "Còn mở"
    if issue["resolved"] and data.has("issues", "resolution_hours") and pd.notna(issue["resolution_hours"]):
        status += f" sau {issue['resolution_hours']:.1f} giờ"
    rows.append(("Trạng thái", status))
    return pd.DataFrame(rows, columns=["Mục", "Giá trị"])


def _handling(issue: pd.Series, data: store.Tables) -> None:
    """Thẻ cuối trang: issue này đã được xử lý thế nào."""
    if data.available("patches"):
        patch = data["patches"][data["patches"]["issue_id"] == issue.name]
        if not patch.empty:
            p = patch.iloc[0]
            with st.container(border=True):
                st.markdown(f"**Bản vá {p['patch_id']}** · {p['operation']} · {p['decision']}")
                st.caption("Đã ghi vào CVAT." if p["applied"] else "Chưa ghi vào CVAT.")
            return
    if data.has("issues", "fix_arm", "fix_outcome") and issue["fix_arm"] == S.ARM_ANNOTATOR \
            and pd.notna(issue["fix_outcome"]):
        with st.container(border=True):
            st.markdown(f"**{S.ARM_ANNOTATOR}** · {issue['fix_outcome']}")
            if data.has("issues", "observed_change") and pd.notna(issue["observed_change"]):
                st.caption(f"Thay đổi thực tế trên annotation: {issue['observed_change']}")


def render():
    data, f = store.load(), ui.filters()
    issues = f.apply(data["issues"])
    if issues.empty:
        return ui.empty()

    c1, c2, c3 = st.columns([1.2, 1, 2.6], vertical_alignment="bottom")
    kind = c1.selectbox("Loại lỗi", [ALL, *S.ERROR_TYPES], key="detail_type")
    reviewer = c2.selectbox("Reviewer", [ALL, *sorted(issues["reviewer"].unique())], key="detail_reviewer")
    if kind != ALL:
        issues = issues[issues["error_type"] == kind]
    if reviewer != ALL:
        issues = issues[issues["reviewer"] == reviewer]
    if issues.empty:
        return ui.empty()
    listed = issues.head(MAX_LISTED).set_index("issue_id")
    pick = c3.selectbox(
        f"Issue ({len(issues):,} khớp bộ lọc" + (f", hiện {MAX_LISTED} đầu)" if len(issues) > MAX_LISTED else ")"),
        list(listed.index), key="detail_issue",
        format_func=lambda i: f"{i} · {listed.at[i, 'annotator']} · {listed.at[i, 'error_type']} · {listed.at[i, 'class_name']}")
    issue = listed.loc[pick]

    left, right = st.columns([3, 2])
    with left, st.container(border=True, height="stretch"):
        has_truth = data.has("issues", "gx1")
        show_truth = st.toggle("Hiện đáp án", key="detail_truth", disabled=not has_truth) and has_truth
        spot, submitted, truth = images.box_of(issue, "i"), images.box_of(issue, "s"), images.box_of(issue, "g")
        boxes = [(spot, theme.BOX_ISSUE), (submitted, theme.BOX_SUBMITTED)]
        if show_truth:
            boxes.append((truth, theme.BOX_TRUTH))
        picture = images.crop(issue["image"], boxes, frame=[spot, submitted] + ([truth] if show_truth else []),
                              min_width=640)
        if picture is None:
            st.caption("Không tìm thấy ảnh trong file zip.")
        else:
            st.image(picture, width="stretch")
        legend = []
        if spot is not None:
            legend.append("Trắng: vùng reviewer đánh dấu.")
        if submitted is not None:
            legend.append("Cam: box annotator đã nộp.")
        elif data.has("issues", "sx1"):
            legend.append("Annotator không vẽ box nào ở đây.")
        if show_truth:
            legend.append("Xanh dương: đáp án.")
        st.caption(" ".join([*legend, f"Ảnh: {issue['image']}"]))
    with right:
        with st.container(border=True):
            st.markdown(f"**Reviewer {issue['reviewer']}** · {issue['created_at']:%d/%m %H:%M}")
            st.write(issue["comment"] if pd.notna(issue["comment"]) else "(issue không có nội dung)")
            if data.has("issues", "reply") and pd.notna(issue["reply"]):
                st.markdown(f"**Annotator {issue['annotator']}**")
                st.write(issue["reply"])
        facts = _facts(issue, data)
        st.dataframe(facts, hide_index=True, width="stretch", height=ROW_PX * (len(facts) + 1) + 3)
    _handling(issue, data)
