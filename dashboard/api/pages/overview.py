"""Tổng quan: năm con số chính, xu hướng theo job và ba bảng xếp hạng ngắn."""
import settings as S
from api import blocks as B
from data_layer import metrics, store
from data_layer.filters import Filters
from ui import charts

RATE = "Issue trên 100 vật đã review"
RECURRENCE, RESOLUTION = "Lỗi lặp lại", "Trung vị xử lý"  # hai KPI của đề M22


def build(data: store.Tables, f: Filters) -> list[dict]:
    issues, work = f.apply(data["issues"]), f.apply(data["workload"])
    if issues.empty or work.empty:
        return [B.row(B.empty())]

    done = issues[issues["resolved"]]
    recurrence = f"{issues['is_recurrent'].mean():.0%}" if data.has("issues", "is_recurrent") else None
    timed = data.has("issues", "resolution_hours") and done["resolution_hours"].notna().any()
    rows = [B.row(B.kpis([
        (RECURRENCE, recurrence, "Tỷ lệ issue mà cùng annotator đã mắc cùng loại lỗi ở một job trước đó."),
        (RESOLUTION, f"{done['resolution_hours'].median():.1f} giờ" if timed else None,
         "Trung vị thời gian từ lúc mở đến lúc đóng, tính trên các issue đã đóng."),
        ("Tổng issue", f"{len(issues):,}", "Số issue reviewer đã mở trong phạm vi đang lọc."),
        ("Issue / 100 vật", f"{len(issues) / work['n_reviewed'].sum() * 100:.1f}",
         "Issue trên 100 vật đã review. Mẫu số gồm annotation đã review và vật bị báo thiếu, "
         "để class bị bỏ sót nhiều không làm tỷ lệ vọt lên."),
        ("Chưa xử lý", f"{1 - issues['resolved'].mean():.0%}", "Tỷ lệ issue còn mở."),
    ], primary=(RECURRENCE, RESOLUTION)))]

    trend = metrics.rate(issues, work, ["job_order"])
    trend["job"] = "Job " + trend["job_order"].astype(str)
    left = B.chart(
        "Tỷ lệ issue qua từng job",
        charts.line(trend, "job", "rate", x_title="Thứ tự job của annotator", x_order=list(trend["job"]),
                    y_title=RATE),
        note="Đường đi xuống nghĩa là lỗi ít dần theo thời gian.",
        table=trend[["job", "n_issues", "n_reviewed", "rate"]].round(1),
    )
    title = "Lỗi được quy về nguồn nào"
    right = B.ready(data, title, issues=["attributed_source"])
    if right is None:
        src = (issues["attributed_source"].value_counts().reindex(S.SOURCES, fill_value=0)
               .rename_axis("source").reset_index(name="n"))
        right = B.chart(title, charts.hbar(src, "source", "n", x_title="Số issue", order=S.SOURCES, name="Nguồn lỗi"),
                        note="Kết quả của agent quy nguồn, gom theo cụm lỗi.", table=src)
    rows.append(B.row(left, right, widths=[3, 2]))

    top = issues["error_type"].value_counts().head(5).rename_axis("error_type").reset_index(name="n")
    by_class = metrics.rate(issues, work, ["class_name"])
    by_class = by_class[~by_class["low_n"]].nlargest(5, "rate")
    rows.append(B.row(
        B.chart("Năm loại lỗi nhiều nhất", charts.hbar(top, "error_type", "n", x_title="Số issue", name="Loại lỗi"),
                table=top),
        B.chart("Năm class khó nhất",
                charts.hbar(by_class, "class_name", "rate", x_title=RATE, fmt=".1f", name="Class"),
                note=f"Bỏ qua class có dưới {S.MIN_REVIEWED} vật đã review.",
                table=by_class[["class_name", "n_issues", "n_reviewed", "rate"]].round(1)),
    ))
    return rows
