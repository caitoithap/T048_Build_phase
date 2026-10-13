"""Đề xuất vs sửa, phần 2: bản vá agent đưa ra và quyết định của người duyệt."""
import altair as alt
import pandas as pd
import streamlit as st

import settings as S
from data_layer import store
from ui import charts, images, theme
from ui import components as ui

META = dict(
    title="Agent đề xuất vs người áp dụng", icon=":material/smart_toy:", path="sua-agent",
    question="Đề xuất sửa của agent có đúng không, và người duyệt có lọc được đề xuất sai?",
    tables=["patches", "issues"], requires={"patches": []}, filters={"run", "class", "annotator"},
)
HUMAN = S.DECISIONS[:3]  # ba quyết định do người đưa ra
ACCEPTED = S.DECISIONS[0]
RIGHT, WRONG = "Agent đề xuất đúng", "Agent đề xuất sai"


def _funnel(patches: pd.DataFrame) -> pd.DataFrame:
    steps = [
        ("Issue vào luồng agent", len(patches)),
        ("Map được vào annotation", int(patches["mapped"].sum())),
        ("Agent đưa ra đề xuất", int(patches["proposed"].sum())),
        ("Người đã quyết định", int(patches["decision"].isin(HUMAN).sum())),
        ("Được chấp nhận", int(patches["decision"].isin(HUMAN[:2]).sum())),
        ("Đã ghi vào CVAT", int(patches["applied"].sum())),
        ("Reviewer đóng issue", int(patches["issue_closed"].sum())),
    ]
    df = pd.DataFrame(steps, columns=["step", "n"])
    kept = (df["n"] / df["n"].shift(1).replace(0, 1)).fillna(1)
    df["label"] = [f"{n:,}" if i == 0 else f"{n:,} · giữ {k:.0%}" for i, (n, k) in enumerate(zip(df["n"], kept))]
    return df


def _strip(patch: pd.Series, issue: pd.Series, show_truth: bool) -> None:
    """Ba ảnh cắt cùng một vùng: trước khi sửa, agent đề xuất, sau khi áp dụng."""
    spot, submitted, truth = images.box_of(issue, "i"), images.box_of(issue, "s"), images.box_of(issue, "g")
    proposed, final = images.box_of(patch, "p"), images.box_of(patch, "f")
    frame = [spot, submitted, proposed, final] + ([truth] if show_truth else [])
    extra = [(truth, theme.BOX_TRUTH)] if show_truth else []
    panels = [
        ("Trước khi sửa", submitted, theme.BOX_SUBMITTED, issue["class_pred"]),
        ("Agent đề xuất", proposed, theme.BOX_PROPOSED, patch["proposed_class"]),
        ("Sau khi áp dụng", final, theme.BOX_FINAL, patch["final_class"]),
    ]
    for col, (title, box, color, cls) in zip(st.columns(3), panels):
        with col:
            st.markdown(f"**{title}**")
            picture = images.crop(issue["image"], [*extra, (box, color)], frame=frame, min_width=420)
            if picture is None:
                st.caption("Không tìm thấy ảnh.")
            else:
                st.image(picture, width="stretch")
            if box is None:
                st.caption("Không có box")
            elif pd.notna(cls):
                st.caption(f"Class: {cls}")


def _one_patch(data: store.Tables, decided: pd.DataFrame) -> None:
    st.subheader("Xem một bản vá", anchor=False)
    shown = decided.head(300)
    if shown.empty or not ui.ready(data, "Ảnh trước và sau", issues=[]):
        return
    by_id = shown.set_index("patch_id")
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    pick = c1.selectbox(
        "Bản vá", list(by_id.index), key="agent_patch",
        format_func=lambda p: f"{p} · {by_id.at[p, 'operation']} · {by_id.at[p, 'decision']} · {by_id.at[p, 'class_name']}")
    show_truth = c2.toggle("Hiện đáp án", key="agent_truth", disabled=not data.has("issues", "gx1"))
    patch = by_id.loc[pick]
    issues = data["issues"].set_index("issue_id")
    if patch["issue_id"] not in issues.index:
        return ui.empty(f"Bảng issues không có issue {patch['issue_id']} của bản vá này.")
    issue = issues.loc[patch["issue_id"]]
    with st.container(border=True):
        _strip(patch, issue, show_truth)
        legend = "Cam: box đã nộp. Xanh lá: box agent đề xuất. Vàng: box sau khi áp dụng."
        st.caption(legend + (" Xanh dương: đáp án." if show_truth else ""))
        if pd.notna(issue["comment"]):
            st.markdown(f"**Reviewer {issue['reviewer']}:** {issue['comment']}")


def render():
    data, f = store.load(), ui.filters()
    patches = f.apply(data["patches"])
    if patches.empty:
        return ui.empty()
    ui.simulated("Phần này chỉ có nghĩa khi quyết định chấp nhận hay từ chối do người trong nhóm bấm thật, "
                 "và màn hình duyệt không hiện đáp án. Trong dữ liệu giả, các quyết định này là số tự sinh.")

    checked = data.has("patches", "proposal_correct")
    proposed = patches[patches["proposed"]]
    decided = patches[patches["decision"].isin(HUMAN)]
    right_share = slipped = None
    if checked:
        right_share = f"{proposed['proposal_correct'].mean():.0%}" if len(proposed) else "–"
        slipped = f"{int(((decided['decision'] == ACCEPTED) & ~decided['proposal_correct']).sum()):,}"
    ui.kpi_row([
        ("Vào luồng agent", f"{len(patches):,}", "Số issue được giao cho agent đề xuất cách sửa."),
        ("Có đề xuất", f"{len(proposed) / len(patches):.0%}", "Phần issue mà agent đưa ra được bản vá."),
        ("Duyệt nguyên văn", f"{(decided['decision'] == ACCEPTED).mean():.0%}" if len(decided) else "–",
         "Trong số đề xuất đã có quyết định, bao nhiêu phần được chấp nhận mà không sửa."),
        ("Đề xuất đúng", right_share, "So với đáp án."),
        ("Đề xuất sai lọt qua", slipped, "Đề xuất sai nhưng vẫn được chấp nhận nguyên văn. Cần đáp án."),
    ])

    left, right = st.columns(2)
    with left:
        funnel = _funnel(patches)
        ui.chart("Từ issue đến bản vá đã ghi",
                 charts.hbar(funnel, "step", "n", order=list(funnel["step"]), label="label", x_title="Số issue",
                             name="Bước"),
                 note="\"Giữ\" là phần còn lại so với bước ngay trước.", table=funnel)
    with right:
        title = "Đề xuất của agent × quyết định của người"
        if ui.ready(data, title, patches=["proposal_correct"]):
            if decided.empty:
                ui.empty("Chưa có đề xuất nào được quyết định.")
            else:
                verdict = decided["proposal_correct"].map({True: RIGHT, False: WRONG})
                grid = pd.MultiIndex.from_product([[RIGHT, WRONG], HUMAN], names=["agent", "human"])
                cells = (decided.groupby([verdict, "decision"]).size()
                         .reindex(grid, fill_value=0).rename("n").reset_index())
                cells["share"] = cells["n"] / cells.groupby("agent")["n"].transform("sum").replace(0, 1)
                cells["label"] = [f"{n:,} ({s:.0%})" for n, s in zip(cells["n"], cells["share"])]
                ui.chart(
                    title,
                    charts.heatmap(cells, "human", "agent", "share", fmt=".0%", label="label", x_order=HUMAN,
                                   y_order=[RIGHT, WRONG], x_title="Quyết định của người duyệt", step=64, vmax=1.0,
                                   show_legend=False,
                                   tooltip=[alt.Tooltip("agent:N", title="Agent"),
                                            alt.Tooltip("human:N", title="Người duyệt"),
                                            alt.Tooltip("n:Q", title="Số đề xuất"),
                                            alt.Tooltip("share:Q", title="Phần của hàng", format=".0%")]),
                    note=f"Mỗi hàng cộng lại bằng 100%. Ô cần để ý: hàng dưới, cột \"{ACCEPTED}\" là đề xuất sai "
                         "lọt qua người duyệt.",
                    table=cells[["agent", "human", "n", "share"]].round(3),
                )

    by_op = proposed.groupby(["operation", "decision"]).size().reset_index(name="n")
    ui.chart(
        "Quyết định theo loại thao tác",
        charts.hbar_stacked(by_op, "operation", "decision", "n", series_order=S.DECISIONS, y_order=S.ACTIONS,
                            name="Thao tác", series_title="Quyết định", value_title="Số đề xuất"),
        note="Thao tác nào bị từ chối hoặc phải sửa lại nhiều thì agent chưa làm tốt thao tác đó.",
        table=by_op,
    )
    _one_patch(data, decided)
