"""Chấm chéo, phần 2: reviewer nào chấm annotator nào, và độ khó của reviewer."""
import pandas as pd
import settings as S
from api import blocks as B
from data_layer import metrics, store
from data_layer.filters import Filters
from ui import charts

BOTH, ONLY_A, ONLY_B = "Cả hai cùng báo", "Chỉ người thứ nhất", "Chỉ người thứ hai"
RATE = "Issue / 100 vật"


def build(data: store.Tables, f: Filters) -> list[dict]:
    issues, work = f.apply(data["issues"]), f.apply(data["workload"])
    if issues.empty or work.empty:
        return [B.row(B.empty())]

    assign = f.apply(data["review_assignments"]) if data.available("review_assignments") else None
    overlap = f.apply(data["reviewer_overlap"]) if data.available("reviewer_overlap") else None
    twice = alarms = shared = None
    if assign is not None and data.has("review_assignments", "is_second_review"):
        twice = f"{int(assign['is_second_review'].sum())}"
    if assign is not None and data.has("review_assignments", "n_false_alarms"):
        alarms = f"{assign['n_false_alarms'].sum() / max(assign['n_issues'].sum(), 1):.0%}"
    if overlap is not None and not overlap.empty:
        counts = overlap[["n_both", "n_only_a", "n_only_b"]].sum()
        shared = f"{counts['n_both'] / max(counts.sum(), 1):.0%}"

    rows = [
        B.row(B.notice(
            "Khi reviewer là mô phỏng, các con số ở trang này chỉ hiện lại tham số đã đặt. "
            "Chúng cho biết pipeline tính đúng; phải có người review thật thì mới đọc ra điều mới.",
            tone="simulated"
        )),
        B.row(B.kpis([
            ("Lượt chấm", None if assign is None else f"{len(assign)}",
             "Mỗi lượt là một reviewer chấm một job, tính cả job không có issue."),
            ("Job được chấm hai lần", twice, None),
            ("Issue báo nhầm", alarms, "Phần issue mà annotation vốn đúng. Cần đáp án mới tính được."),
            ("Trùng nhau khi cùng chấm", shared, "Trong số vật ít nhất một người báo, bao nhiêu phần cả hai cùng báo."),
        ]))
    ]

    cell = metrics.rate(issues, work, ["reviewer", "annotator"])
    reviewers, annotators = sorted(cell["reviewer"].unique()), sorted(cell["annotator"].unique())
    full = pd.MultiIndex.from_product([reviewers, annotators], names=["reviewer", "annotator"])
    grid = cell.set_index(["reviewer", "annotator"]).reindex(full).reset_index()
    grid["low_n"] = grid["n_reviewed"].fillna(0) < S.MIN_REVIEWED

    main_chart = B.chart(
        "Reviewer × annotator",
        charts.heatmap(grid, "annotator", "reviewer", "rate", low_n="low_n", x_order=annotators, y_order=reviewers,
                       x_title="Annotator", y_title="Reviewer", value_title=RATE, step=44),
        note="Một hàng đậm đều là reviewer khó. Một cột đậm đều là annotator yếu. Ô xám là cặp chưa đủ mẫu.",
        table=cell.round(1),
    )
    rows.append(B.row(main_chart))

    by_reviewer = metrics.rate(issues, work, ["reviewer"]).set_index("reviewer")
    strictness = by_reviewer["rate"] / max((len(issues) / work["n_reviewed"].sum() * 100), 0.001)

    cell["adjusted"] = cell["n_issues"] / cell["reviewer"].map(strictness).replace(0, 1)
    people = cell.groupby("annotator", as_index=False)[["n_issues", "adjusted", "n_reviewed"]].sum()
    people["raw"] = people["n_issues"] / people["n_reviewed"].replace(0, 1) * 100
    people["fair"] = people["adjusted"] / people["n_reviewed"].replace(0, 1) * 100
    left = B.chart(
        "Tỷ lệ issue của annotator, trước và sau khi trừ độ khó của reviewer",
        charts.dumbbell(people, "annotator", "raw", "fair", start_name="Tỷ lệ thô",
                        end_name="Đã trừ độ khó của reviewer", x_title="Issue trên 100 vật đã review",
                        row_order=annotators, name="Annotator"),
        note="Chấm dịch xa nghĩa là annotator đó gặp reviewer khó hoặc dễ hơn mặt bằng chung.",
        table=people[["annotator", "raw", "fair"]].round(1),
    )

    right = B.ready(data, "Hai reviewer chấm cùng một job", reviewer_overlap=[])
    if right is None and overlap is not None:
        if overlap.empty:
            right = B.empty("Chưa có job nào được hai reviewer cùng chấm trong bộ lọc hiện tại.")
        else:
            both = overlap.assign(pair=overlap["reviewer_a"] + " và " + overlap["reviewer_b"])
            both = both.groupby("pair", as_index=False)[["n_both", "n_only_a", "n_only_b"]].sum()
            both = both.melt(id_vars="pair", var_name="kind", value_name="n")
            both["kind"] = both["kind"].map({"n_both": BOTH, "n_only_a": ONLY_A, "n_only_b": ONLY_B})
            right = B.chart(
                "Hai reviewer chấm cùng một job",
                charts.hbar_stacked(both, "pair", "kind", "n", series_order=[BOTH, ONLY_A, ONLY_B],
                                    name="Cặp reviewer", series_title="Ai báo", value_title="Số vật"),
                note="Phần \"cả hai cùng báo\" càng nhỏ thì hai reviewer càng hiểu tiêu chí khác nhau.",
                table=both,
            )
    rows.append(B.row(left, right, widths=[1, 1]))

    # Bảng hồ sơ reviewer
    table_block = B.ready(data, "Hồ sơ reviewer", review_assignments=[])
    if table_block is None and assign is not None:
        profile = assign.groupby("reviewer", as_index=False).agg(
            jobs=("job_id", "size"), annotations=("n_annotations", "sum"), issues=("n_issues", "sum"))
        profile["strictness"] = profile["reviewer"].map(strictness)
        if data.has("reviewers", "style"):
            profile = profile.merge(data["reviewers"], on="reviewer", how="left")
        by_rev = assign.groupby("reviewer")
        if data.has("review_assignments", "n_false_alarms"):
            alarms_s = profile["reviewer"].map(by_rev["n_false_alarms"].sum())
            profile["alarm_pct"] = alarms_s / profile["issues"].clip(lower=1) * 100
            if data.has("review_assignments", "n_true_errors"):
                errors_s = profile["reviewer"].map(by_rev["n_true_errors"].sum())
                profile["catch_pct"] = (profile["issues"] - alarms_s) / errors_s.clip(lower=1) * 100
        table_block = B.table("Hồ sơ reviewer", profile.round(2), note="Cột báo nhầm và cột bắt được lỗi thật cần đáp án.")
        rows.append(B.row(table_block))

    return rows
