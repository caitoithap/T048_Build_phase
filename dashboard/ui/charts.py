"""Các dạng biểu đồ dùng lại giữa các trang (Altair).

Quy ước: cường độ dùng một màu từ nhạt tới đậm; nhóm dùng màu phân loại theo thứ tự cố định;
thanh mảnh, có khe hở giữa các đoạn; chữ luôn dùng màu mực, không dùng màu dữ liệu.

Màu chữ đặt trên mảng màu được chọn bằng điều kiện, không lấy từ một cột dữ liệu:
Vega-Lite 6.1 lỗi biên dịch khi một lớp có thang màu liên tục còn lớp khác dùng cột màu
với `scale=None`.
"""
from __future__ import annotations

import json

import altair as alt
import numpy as np
import pandas as pd

from ui import theme

_AXIS_Y = dict(domain=False, ticks=False, labelPadding=8, labelLimit=260)


def _fmt(value, fmt: str) -> str:
    return "–" if pd.isna(value) else format(value, fmt)


def _field(name: str) -> str:
    """Tham chiếu một cột trong biểu thức Vega, an toàn với tên có dấu cách."""
    return f"datum[{json.dumps(name, ensure_ascii=False)}]"


def heatmap(df, x, y, value, *, x_title=None, y_title=None, value_title="", fmt=".1f", x_order=None,
            y_order=None, low_n=None, label=None, tooltip=None, step=36, vmax=None, x_angle=0, show_legend=True):
    """Lưới ô màu. Ô thiếu mẫu (`low_n`) tô xám và ghi "ít mẫu" thay cho số.

    `show_legend=False` khi mọi ô đã ghi số, để dành chỗ cho nhãn cột.
    """
    t = theme.tokens()
    d = df.copy()
    low = d[low_n].astype(bool) if low_n else pd.Series(False, index=d.index)
    d["_low"] = low | d[value].isna()
    seen = d.loc[~d["_low"], value].max()
    top = vmax or (float(seen) if pd.notna(seen) and seen > 0 else 1.0)
    d["_label"] = d[label] if label else [("ít mẫu" if lo else _fmt(v, fmt)) for v, lo in zip(d[value], d["_low"])]

    # labelFlush=False: không để Vega ép nhãn cột đầu và cột cuối lệch khỏi tâm cột.
    x_axis = dict(orient="top", domain=False, ticks=False, labelPadding=6, labelAngle=x_angle, labelLimit=140,
                  labelOverlap=False, labelFlush=False)
    if x_angle:
        x_axis["labelAlign"] = "left"
    legend = alt.Legend(title=value_title, gradientLength=120, format=fmt) if show_legend else None
    base = alt.Chart(d).encode(
        x=alt.X(f"{x}:N", sort=x_order, title=x_title, axis=alt.Axis(**x_axis)),
        y=alt.Y(f"{y}:N", sort=y_order, title=y_title, axis=alt.Axis(**_AXIS_Y)),
    )
    stops = [float(v) for v in np.linspace(0, top, len(t["seq"]))]
    cells = base.mark_rect(stroke=t["surface"], strokeWidth=2, cornerRadius=3).encode(
        color=alt.condition(
            "datum._low", alt.value(t["neutral"]),
            alt.Color(f"{value}:Q", scale=alt.Scale(domain=stops, range=t["seq"], clamp=True), legend=legend)),
        tooltip=tooltip or [alt.Tooltip(f"{y}:N", title=y_title or y), alt.Tooltip(f"{x}:N", title=x_title or x),
                            alt.Tooltip(f"{value}:Q", title=value_title or value, format=fmt)],
    )
    ink = alt.value(t["on_weak"], condition=[
        {"test": "datum._low", "value": t["ink2"]},
        {"test": f"{_field(value)} >= {0.5 * top}", "value": t["on_strong"]},
    ])
    labels = base.mark_text(fontSize=12).encode(text="_label:N", color=ink)
    return (cells + labels).properties(height=alt.Step(step))


def hbar(df, y, x, *, x_title="", fmt=",.0f", order=None, label=None, highlight=None, name=None, step=30):
    """Thanh ngang một chuỗi, số ghi ở đầu thanh.

    `highlight`: cột bool, thanh False chìm về xám. `name`: tên của chiều hàng, hiện trong tooltip.
    """
    t = theme.tokens()
    d = df.copy()
    d["_label"] = d[label] if label else d[x].map(lambda v: _fmt(v, fmt))
    order = list(order) if order is not None else list(d.sort_values(x, ascending=False)[y])
    base = alt.Chart(d).encode(
        y=alt.Y(f"{y}:N", sort=order, title=None, axis=alt.Axis(**_AXIS_Y)),
        x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(format=fmt, tickCount=4, domain=False, ticks=False)),
    )
    color = alt.value(t["accent"]) if highlight is None else alt.condition(
        _field(highlight), alt.value(t["accent"]), alt.value(t["deemph"]))
    bars = base.mark_bar(size=16, cornerRadiusEnd=4).encode(
        color=color,
        tooltip=[alt.Tooltip(f"{y}:N", title=name or y), alt.Tooltip(f"{x}:Q", title=x_title or x, format=fmt)])
    text = base.mark_text(align="left", dx=6, fontSize=12, color=t["ink2"]).encode(text="_label:N")
    return (bars + text).properties(height=alt.Step(step))


def hbar_stacked(df, y, series, value, *, series_order, colors=None, normalize=True, y_order=None, x_title="",
                 axis_format=None, labels=True, name=None, series_title="Nhóm", value_title="Số lượng",
                 legend_columns=0, step=34):
    """Thanh ngang xếp chồng. Vị trí từng đoạn tính sẵn; nhãn chỉ hiện ở đoạn đủ rộng để chứa chữ.

    `legend_columns`: số cột của chú giải; 0 là một hàng. Đặt 2 khi thẻ hẹp mà có bốn nhóm.
    """
    t = theme.tokens()
    colors = colors or t["cat"][:len(series_order)]
    d = df.copy()
    d["_rank"] = d[series].map({s: i for i, s in enumerate(series_order)})
    d = d.sort_values([y, "_rank"])
    total = d.groupby(y)[value].transform("sum")
    d["_share"] = np.where(total > 0, d[value] / total, 0.0)
    length = d["_share"] if normalize else d[value]
    d["_x1"] = length.groupby(d[y]).cumsum()
    d["_x0"] = d["_x1"] - length
    d["_xm"] = (d["_x0"] + d["_x1"]) / 2
    span = 1.0 if normalize else float(total.max() or 1)
    # Đoạn chiếm trọn hàng thì "100%" không nói thêm gì, bỏ.
    fits = labels & (length / span >= 0.08) & (d["_share"] < 0.995)
    d["_label"] = np.where(fits, (d["_share"] * 100).round().astype(int).astype(str) + "%", "")

    y_enc = alt.Y(f"{y}:N", sort=y_order, title=None, axis=alt.Axis(**_AXIS_Y))
    x_scale = alt.Scale(domain=[0, 1]) if normalize else alt.Undefined
    bars = alt.Chart(d).mark_bar(size=18, stroke=t["surface"], strokeWidth=2).encode(
        y=y_enc,
        x=alt.X("_x0:Q", title=x_title, scale=x_scale,
                axis=alt.Axis(format=axis_format or (".0%" if normalize else ",.0f"), tickCount=4, domain=False, ticks=False)),
        x2="_x1:Q",
        color=alt.Color(f"{series}:N", scale=alt.Scale(domain=series_order, range=colors),
                        legend=alt.Legend(orient="top", title=None, columns=legend_columns)),
        tooltip=[alt.Tooltip(f"{y}:N", title=name or y), alt.Tooltip(f"{series}:N", title=series_title),
                 alt.Tooltip(f"{value}:Q", title=value_title, format=",.4~g"),
                 alt.Tooltip("_share:Q", title="Tỷ trọng trong hàng", format=".0%")],
    )
    on_dark_fill = [s for s, c in zip(series_order, colors) if theme.ink_on(c) == "#ffffff"]
    ink = alt.value("#0b0b0b", condition={
        "test": f"indexof({json.dumps(on_dark_fill, ensure_ascii=False)}, {_field(series)}) >= 0", "value": "#ffffff"})
    text = alt.Chart(d).mark_text(fontSize=11).encode(y=y_enc, x="_xm:Q", text="_label:N", color=ink)
    return (bars + text).properties(height=alt.Step(step))


def line(df, x, y, *, x_title="", y_title="", fmt=".1f", x_order=None, height=250):
    t = theme.tokens()
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:N", sort=x_order, title=x_title, axis=alt.Axis(labelAngle=0, domain=False, ticks=False)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=alt.Scale(zero=True),
                axis=alt.Axis(format=fmt, tickCount=4, domain=False, ticks=False)),
    )
    path = base.mark_line(strokeWidth=2, color=t["accent"], strokeJoin="round", strokeCap="round")
    dots = base.mark_circle(size=80, opacity=1, color=t["accent"], stroke=t["surface"], strokeWidth=2).encode(
        tooltip=[alt.Tooltip(f"{x}:N", title=x_title or x), alt.Tooltip(f"{y}:Q", title=y_title or y, format=fmt)])
    return (path + dots).properties(height=height)


def dumbbell(df, row, start, end, *, start_name, end_name, x_title="", fmt=".1f", row_order=None, name="Hàng", step=34):
    """Trước và sau của từng hàng: hai chấm cùng tông màu, nối bằng một đoạn xám."""
    t = theme.tokens()
    long = df.melt(id_vars=[row], value_vars=[start, end], var_name="_series", value_name="_value")
    long["_series"] = long["_series"].map({start: start_name, end: end_name})
    y_enc = alt.Y(f"{row}:N", sort=row_order, title=None, axis=alt.Axis(**{**_AXIS_Y, "labelLimit": 380}))
    x_axis = alt.Axis(format=fmt, tickCount=5, domain=False, ticks=False, labelFlush=True)
    link = alt.Chart(df.dropna(subset=[start, end])).mark_rule(strokeWidth=2, color=t["deemph"]).encode(
        y=y_enc, x=alt.X(f"{start}:Q", title=x_title, axis=x_axis), x2=f"{end}:Q")
    dots = alt.Chart(long.dropna(subset=["_value"])).mark_circle(
        size=120, opacity=1, stroke=t["surface"], strokeWidth=2).encode(
        y=y_enc, x=alt.X("_value:Q", title=x_title, axis=x_axis),
        color=alt.Color("_series:N", scale=alt.Scale(domain=[start_name, end_name], range=list(t["pair"])),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip(f"{row}:N", title=name), alt.Tooltip("_series:N", title="Lần"),
                 alt.Tooltip("_value:Q", title=x_title or "Giá trị", format=fmt)],
    )
    return (link + dots).properties(height=alt.Step(step))


def scatter(df, x, y, *, x_title="", y_title="", fmt=".0%", label=None, tooltip=None, size=110, opacity=1.0, height=300):
    """Biểu đồ điểm một chuỗi. `label`: cột ghi tên cạnh từng điểm (chỉ dùng khi ít điểm)."""
    t = theme.tokens()
    axis = dict(format=fmt, tickCount=5, domain=False, ticks=False)
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:Q", title=x_title, scale=alt.Scale(zero=False, nice=True), axis=alt.Axis(**axis)),
        y=alt.Y(f"{y}:Q", title=y_title, scale=alt.Scale(zero=False, nice=True), axis=alt.Axis(**axis)),
    )
    dots = base.mark_circle(size=size, opacity=opacity, color=t["accent"], stroke=t["surface"], strokeWidth=2).encode(
        tooltip=tooltip or [alt.Tooltip(f"{x}:Q", title=x_title, format=fmt), alt.Tooltip(f"{y}:Q", title=y_title, format=fmt)])
    if label is None:
        return dots.properties(height=height)
    names = base.mark_text(align="left", dx=9, dy=1, fontSize=12, color=t["ink2"]).encode(text=f"{label}:N")
    return (dots + names).properties(height=height)
