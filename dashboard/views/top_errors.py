"""Top lỗi: loại lỗi nào nhiều nhất, lặp lại nhiều nhất và xử lý lâu nhất."""
import streamlit as st

from data_layer import store
from ui import charts, theme
from ui import components as ui

META = dict(
    title="Top lỗi", icon=":material/leaderboard:", path="top-loi",
    question="Loại lỗi nào xuất hiện nhiều nhất, và loại nào cứ lặp lại?",
    tables=["issues"], requires={"issues": []}, filters={"run", "class", "size", "annotator"},
)
REPEAT, FIRST = "Lặp lại", "Lần đầu"


def render():
    data, f = store.load(), ui.filters()
    issues = f.apply(data["issues"])
    if issues.empty:
        return ui.empty()
    recur, timed = data.has("issues", "is_recurrent"), data.has("issues", "resolution_hours")

    by_type = issues.groupby("error_type")
    summary = by_type.size().rename("n").reset_index().sort_values("n", ascending=False)
    summary["open"] = summary["error_type"].map((1 - by_type["resolved"].mean()) * 100)
    order = list(summary["error_type"])

    if recur:
        summary["repeat"] = summary["error_type"].map(by_type["is_recurrent"].mean() * 100)
        t = theme.tokens()
        split = (issues.assign(kind=issues["is_recurrent"].map({True: REPEAT, False: FIRST}))
                 .groupby(["error_type", "kind"]).size().reset_index(name="n"))
        ui.chart(
            "Số issue theo loại lỗi, tách phần lặp lại",
            charts.hbar_stacked(split, "error_type", "kind", "n", series_order=[REPEAT, FIRST],
                                colors=[t["accent"], t["deemph"]], normalize=False, y_order=order, x_title="Số issue",
                                name="Loại lỗi", series_title="Loại issue", value_title="Số issue"),
            note="Phần màu đậm là issue lặp lại: cùng annotator đã mắc cùng loại lỗi ở một job trước đó. "
                 "Số phần trăm là tỷ trọng trong loại lỗi đó.",
            table=split,
        )
    else:
        ui.chart(
            "Số issue theo loại lỗi",
            charts.hbar(summary, "error_type", "n", x_title="Số issue", order=order, name="Loại lỗi"),
            note="Chưa tách được phần lặp lại vì bảng issues chưa có cột is_recurrent (chặng D · mart).",
            table=summary[["error_type", "n"]],
        )

    left, right = st.columns([2, 3])
    with left:
        title = "Trung vị thời gian xử lý theo loại lỗi"
        if ui.ready(data, title, issues=["resolution_hours"]):
            hours = by_type["resolution_hours"].median().rename("hours").reset_index().dropna()
            summary["hours"] = summary["error_type"].map(hours.set_index("error_type")["hours"])
            ui.chart(title, charts.hbar(hours, "error_type", "hours", x_title="Giờ", fmt=".1f", name="Loại lỗi"),
                     note="Chỉ tính issue đã đóng.")
    with right:
        columns = {
            "error_type": st.column_config.TextColumn("Loại lỗi", width="medium"),
            "n": st.column_config.NumberColumn("Số issue", width="small"),
        }
        if recur:
            columns["repeat"] = ui.percent_column("Lặp lại")
        if timed and "hours" in summary:
            columns["hours"] = st.column_config.NumberColumn("Trung vị giờ", format="%.1f", width="small")
        columns["open"] = ui.percent_column("Chưa xử lý")
        ui.table("Bảng tổng hợp", summary[list(columns)], column_config=columns)
