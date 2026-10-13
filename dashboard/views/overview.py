"""Tổng quan: năm con số chính, xu hướng theo job và ba bảng xếp hạng ngắn."""
import streamlit as st

import settings as S
from data_layer import metrics, store
from ui import charts
from ui import components as ui

META = dict(
    title="Tổng quan", icon=":material/space_dashboard:", path="tong-quan",
    question="Chất lượng gán nhãn đang ở đâu, và hai KPI của đề (lỗi lặp lại, thời gian xử lý) là bao nhiêu?",
    tables=["issues", "workload"], requires={"issues": [], "workload": []},
    filters={"run", "class", "size", "annotator"},
)
RATE = "Issue trên 100 vật đã review"


def render():
    data, f = store.load(), ui.filters()
    issues, work = f.apply(data["issues"]), f.apply(data["workload"])
    if issues.empty or work.empty:
        return ui.empty()

    done = issues[issues["resolved"]]
    recurrence = f"{issues['is_recurrent'].mean():.0%}" if data.has("issues", "is_recurrent") else None
    timed = data.has("issues", "resolution_hours") and done["resolution_hours"].notna().any()
    ui.kpi_row([
        ("Tổng issue", f"{len(issues):,}", "Số issue reviewer đã mở trong phạm vi đang lọc."),
        ("Issue / 100 vật", f"{len(issues) / work['n_reviewed'].sum() * 100:.1f}",
         "Issue trên 100 vật đã review. Mẫu số gồm annotation đã review và vật bị báo thiếu, "
         "để class bị bỏ sót nhiều không làm tỷ lệ vọt lên."),
        ("Lỗi lặp lại", recurrence, "Tỷ lệ issue mà cùng annotator đã mắc cùng loại lỗi ở một job trước đó."),
        ("Trung vị xử lý", f"{done['resolution_hours'].median():.1f} giờ" if timed else None,
         "Trung vị thời gian từ lúc mở đến lúc đóng, tính trên các issue đã đóng."),
        ("Chưa xử lý", f"{1 - issues['resolved'].mean():.0%}", "Tỷ lệ issue còn mở."),
    ])

    left, right = st.columns([3, 2])
    with left:
        trend = metrics.rate(issues, work, ["job_order"])
        trend["job"] = "Job " + trend["job_order"].astype(str)
        ui.chart(
            "Tỷ lệ issue qua từng job",
            charts.line(trend, "job", "rate", x_title="Thứ tự job của annotator", x_order=list(trend["job"]),
                        y_title=RATE),
            note="Đường đi xuống nghĩa là lỗi ít dần theo thời gian.",
            table=trend[["job", "n_issues", "n_reviewed", "rate"]].round(1),
        )
    with right:
        title = "Lỗi được quy về nguồn nào"
        if ui.ready(data, title, issues=["attributed_source"]):
            src = (issues["attributed_source"].value_counts().reindex(S.SOURCES, fill_value=0)
                   .rename_axis("source").reset_index(name="n"))
            ui.chart(title, charts.hbar(src, "source", "n", x_title="Số issue", order=S.SOURCES, name="Nguồn lỗi"),
                     note="Kết quả của agent quy nguồn, gom theo cụm lỗi.", table=src)

    c1, c2 = st.columns(2)
    with c1:
        top = issues["error_type"].value_counts().head(5).rename_axis("error_type").reset_index(name="n")
        ui.chart("Năm loại lỗi nhiều nhất",
                 charts.hbar(top, "error_type", "n", x_title="Số issue", name="Loại lỗi"), table=top)
    with c2:
        by_class = metrics.rate(issues, work, ["class_name"])
        by_class = by_class[~by_class["low_n"]].nlargest(5, "rate")
        ui.chart("Năm class khó nhất",
                 charts.hbar(by_class, "class_name", "rate", x_title=RATE, fmt=".1f", name="Class"),
                 note=f"Bỏ qua class có dưới {S.MIN_REVIEWED} vật đã review.",
                 table=by_class[["class_name", "n_issues", "n_reviewed", "rate"]].round(1))
