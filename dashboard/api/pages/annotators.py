"""Annotator: ai cần hỗ trợ, cần hỗ trợ về loại lỗi gì."""
import settings as S
from api import blocks as B
from data_layer import metrics, store
from data_layer.filters import Filters
from ui import charts, theme

RATE = "Issue / 100 vật"
NEEDS_HELP = "Cần hỗ trợ"


def build(data: store.Tables, f: Filters) -> list[dict]:
    issues, work = f.apply(data["issues"]), f.apply(data["workload"])
    if issues.empty or work.empty:
        return [B.row(B.empty())]

    people = metrics.rate(issues, work, ["annotator"])
    if data.available("annotators"):
        people = people.merge(data["annotators"], on="annotator", how="left")
    median = people["rate"].median()
    people["ratio"] = people["rate"] / max(median, 0.001)
    people["flag"] = people["ratio"].map(lambda r: NEEDS_HELP if r > S.SUPPORT_RATIO else "Bình thường")
    flagged = list(people.loc[people["flag"] == NEEDS_HELP, "annotator"])

    rows = [
        B.row(B.kpis([
            ("Annotator", f"{len(people)}", None),
            ("Trung vị issue / 100 vật", f"{median:.1f}", "Trung vị của tỷ lệ issue giữa các annotator."),
            (NEEDS_HELP, ", ".join(flagged) or "Không có",
             f"Annotator có tỷ lệ issue cao hơn {S.SUPPORT_RATIO} lần trung vị nhóm."),
        ], primary=(NEEDS_HELP,)))
    ]

    grid = metrics.rate_matrix(issues, work, "annotator", "error_type", S.ERROR_TYPES)
    top_chart = B.chart(
        "Annotator × loại lỗi",
        charts.heatmap(grid, "error_type", "annotator", "rate", low_n="low_n", x_order=S.ERROR_TYPES,
                       x_title="Loại lỗi", y_title="Annotator", value_title=RATE),
        note="Một hàng đậm đều là annotator yếu chung; một ô đậm lẻ là lỗi riêng của annotator đó.",
        table=grid[["annotator", "error_type", "n_issues", "n_reviewed", "rate"]].round(1),
    )
    rows.append(B.row(top_chart))

    cols = ["annotator", "flag", "rate", "ratio"]
    if data.has("issues", "is_recurrent"):
        people["repeat"] = people["annotator"].map(issues.groupby("annotator")["is_recurrent"].mean().mul(100))
        cols.append("repeat")
    cols.append("n_reviewed")
    for col in ("model", "config"):
        if col in people and people[col].notna().any():
            cols.append(col)

    left = B.table("Hồ sơ annotator", people[cols].round(1),
                   note=f"Cờ \"{NEEDS_HELP}\" bật khi tỷ lệ issue vượt {S.SUPPORT_RATIO} lần trung vị nhóm.")

    title = "Issue theo nguồn gốc box"
    right = B.ready(data, title, issues=["source"])
    if right is None:
        t = theme.tokens()
        color_of = dict(zip(S.BOX_SOURCES, [*t["cat"][:len(S.BOX_SOURCES) - 1], t["deemph"]]))
        by_source = issues.groupby(["annotator", "source"]).size().reset_index(name="n")
        present = [s for s in S.BOX_SOURCES if s in set(by_source["source"])]
        right = B.chart(
            title,
            charts.hbar_stacked(by_source, "annotator", "source", "n", series_order=present,
                                colors=[color_of[s] for s in present], name="Annotator",
                                series_title="Nguồn gốc box", value_title="Số issue"),
            note="auto: model vẽ, người không đụng. semi-auto: người đã sửa. manual: người vẽ mới. "
                 "file: nhập từ file. Phần xám là issue báo thiếu vật.",
            table=by_source,
        )

    rows.append(B.row(left, right, widths=[1, 1]))
    return rows
