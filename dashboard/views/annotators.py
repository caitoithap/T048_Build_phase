"""Annotator: ai cần hỗ trợ, cần hỗ trợ về loại lỗi gì."""
import streamlit as st

import catalog
import settings as S
from data_layer import metrics, store
from ui import charts, theme
from ui import components as ui

META = catalog.PAGES["annotator"]
RATE = "Issue / 100 vật"
NEEDS_HELP = "Cần hỗ trợ"


def render():
    data, f = store.load(), ui.filters()
    issues, work = f.apply(data["issues"]), f.apply(data["workload"])
    if issues.empty or work.empty:
        return ui.empty()

    people = metrics.rate(issues, work, ["annotator"])
    if data.available("annotators"):
        people = people.merge(data["annotators"], on="annotator", how="left")
    median = people["rate"].median()
    people["ratio"] = people["rate"] / median
    people["flag"] = people["ratio"].map(lambda r: NEEDS_HELP if r > S.SUPPORT_RATIO else "Bình thường")
    flagged = list(people.loc[people["flag"] == NEEDS_HELP, "annotator"])

    ui.kpi_row([
        ("Annotator", f"{len(people)}", None),
        ("Trung vị issue / 100 vật", f"{median:.1f}", "Trung vị của tỷ lệ issue giữa các annotator."),
        (NEEDS_HELP, ", ".join(flagged) or "Không có",
         f"Annotator có tỷ lệ issue cao hơn {S.SUPPORT_RATIO} lần trung vị nhóm."),
    ])

    grid = metrics.rate_matrix(issues, work, "annotator", "error_type", S.ERROR_TYPES)
    ui.chart(
        "Annotator × loại lỗi",
        charts.heatmap(grid, "error_type", "annotator", "rate", low_n="low_n", x_order=S.ERROR_TYPES,
                       x_title="Loại lỗi", y_title="Annotator", value_title=RATE),
        note="Một hàng đậm đều là annotator yếu chung; một ô đậm lẻ là lỗi riêng của annotator đó.",
        table=grid[["annotator", "error_type", "n_issues", "n_reviewed", "rate"]].round(1),
    )

    columns = {
        "annotator": "Annotator", "flag": "Trạng thái",
        "rate": st.column_config.NumberColumn(RATE, format="%.1f"),
        "ratio": st.column_config.NumberColumn("So với trung vị", format="%.2f lần"),
    }
    if data.has("issues", "is_recurrent"):
        people["repeat"] = people["annotator"].map(issues.groupby("annotator")["is_recurrent"].mean().mul(100))
        columns["repeat"] = ui.percent_column("Lặp lại")
    columns["n_reviewed"] = st.column_config.NumberColumn("Vật đã review")
    for col, label in (("model", "Model"), ("config", "Cấu hình")):
        if col in people and people[col].notna().any():
            columns[col] = label
    ui.table("Hồ sơ annotator", people[list(columns)], column_config=columns,
             note=f"Cờ \"{NEEDS_HELP}\" bật khi tỷ lệ issue vượt {S.SUPPORT_RATIO} lần trung vị nhóm.")

    title = "Issue theo nguồn gốc box"
    if ui.ready(data, title, issues=["source"]):
        # Màu đi theo tên nguồn chứ không theo thứ tự xuất hiện; nguồn nào không có trong dữ liệu thì bỏ khỏi chú giải.
        t = theme.tokens()
        color_of = dict(zip(S.BOX_SOURCES, [*t["cat"][:len(S.BOX_SOURCES) - 1], t["deemph"]]))
        by_source = issues.groupby(["annotator", "source"]).size().reset_index(name="n")
        present = [s for s in S.BOX_SOURCES if s in set(by_source["source"])]
        ui.chart(
            title,
            charts.hbar_stacked(by_source, "annotator", "source", "n", series_order=present,
                                colors=[color_of[s] for s in present], name="Annotator",
                                series_title="Nguồn gốc box", value_title="Số issue"),
            note="auto: model vẽ, người không đụng. semi-auto: người đã sửa. manual: người vẽ mới. "
                 "file: nhập từ file. Phần xám là issue báo thiếu vật.",
            table=by_source,
        )
