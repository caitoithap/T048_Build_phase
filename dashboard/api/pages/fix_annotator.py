"""Đề xuất vs sửa, phần 1: reviewer yêu cầu gì và annotator thực sự sửa gì."""
import altair as alt
import pandas as pd
import settings as S
from api import blocks as B
from data_layer import store
from data_layer.filters import Filters
from ui import charts

CHANGES = [*S.ACTIONS, S.NO_CHANGE]


def build(data: store.Tables, f: Filters) -> list[dict]:
    issues = f.apply(data["issues"])
    mine = issues[issues["fix_arm"] == S.ARM_ANNOTATOR] if "fix_arm" in issues else issues
    done = mine[mine["fix_outcome"] != S.OUTCOME_OPEN] if "fix_outcome" in mine else mine
    if done.empty:
        return [B.row(B.empty())]

    checked = data.has("issues", "is_false_alarm")
    silent = done[done["fix_outcome"] == S.OUTCOME_SILENT] if "fix_outcome" in done else done.iloc[0:0]
    if checked and not silent.empty:
        silent = silent[~silent["is_false_alarm"].eq(True)]
    still_wrong = f"{done['still_wrong'].mean():.0%}" if data.has("issues", "still_wrong") else None

    rows = [
        B.row(B.notice(
            "Khi cách annotator phản hồi issue là mô phỏng, trang này chỉ hiện lại tham số đã đặt. "
            "Với dữ liệu thật, nó cần bản chụp annotation trước và sau khi issue được đóng.",
            tone="simulated"
        )),
        B.row(B.kpis([
            ("Annotator tự xử lý", f"{len(mine):,}", "Số issue không đi qua luồng agent."),
            (S.OUTCOME_RIGHT, f"{(done['fix_outcome'] == S.OUTCOME_RIGHT).mean():.0%}" if "fix_outcome" in done else None, "Tính trên issue đã đóng."),
            (S.OUTCOME_SILENT, f"{len(silent) / max(len(done), 1):.0%}",
             "Issue bị đóng trong khi annotation không đổi. " +
             ("Đã loại issue báo nhầm." if checked else "Chưa loại được issue báo nhầm vì chưa có đáp án.")),
            ("Đóng rồi vẫn sai", still_wrong, "Issue đã đóng mà annotation vẫn sai. Cần đáp án."),
        ]))
    ]

    left = B.empty()
    if "requested_action" in done and "observed_change" in done:
        grid = pd.MultiIndex.from_product([S.ACTIONS, CHANGES], names=["requested", "observed"])
        cells = (done.groupby(["requested_action", "observed_change"]).size()
                 .reindex(grid, fill_value=0).rename("n").reset_index())
        cells["share"] = cells["n"] / cells.groupby("requested")["n"].transform("sum").replace(0, 1)
        left = B.chart(
            "Thao tác được yêu cầu × thay đổi thực tế",
            charts.heatmap(cells, "observed", "requested", "share", fmt=".0%", x_order=CHANGES, y_order=S.ACTIONS,
                           x_title="Thay đổi thực tế trên annotation", y_title="Reviewer yêu cầu", step=44, vmax=1.0,
                           show_legend=False,
                           tooltip=[alt.Tooltip("requested:N", title="Reviewer yêu cầu"),
                                    alt.Tooltip("observed:N", title="Thay đổi thực tế"),
                                    alt.Tooltip("n:Q", title="Số issue"),
                                    alt.Tooltip("share:Q", title="Phần của hàng", format=".0%")]),
            note=f"Mỗi hàng cộng lại bằng 100%. Đường chéo đậm là sửa đúng yêu cầu; cột \"{S.NO_CHANGE}\" đậm là "
                 "đóng issue mà không sửa.",
            table=cells,
        )

    right = B.empty()
    if "fix_outcome" in mine:
        by_person = mine.groupby(["annotator", "fix_outcome"]).size().reset_index(name="n")
        right = B.chart(
            "Kết quả xử lý theo annotator",
            charts.hbar_stacked(by_person, "annotator", "fix_outcome", "n", series_order=S.FIX_OUTCOMES,
                                legend_columns=2, name="Annotator", series_title="Kết quả", value_title="Số issue"),
            note="Tính trên mọi issue annotator tự xử lý, kể cả issue còn mở.",
            table=by_person,
        )
    rows.append(B.row(left, right, widths=[1, 1]))

    cols = [c for c in ["issue_id", "annotator", "reviewer", "class_name", "error_type", "requested_action", "comment"] if c in silent]
    if not silent.empty and cols:
        rows.append(B.row(B.table(
            "Issue bị đóng mà không sửa" + (", trong khi lỗi có thật" if checked else ""),
            silent[cols].head(200),
            note=f"{len(silent):,} issue. Đây là danh sách nên xem lại đầu tiên.",
        )))

    return rows
