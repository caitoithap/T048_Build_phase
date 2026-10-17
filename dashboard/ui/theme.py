"""Màu dùng chung cho biểu đồ, chọn theo chế độ sáng hoặc tối.

API chọn chế độ cho từng request bằng `using(dark)`; bản Streamlit đọc theme đang bật.
Thứ tự màu phân loại là cố định (đã qua kiểm tra mù màu); màu đi theo tên nhóm,
không đi theo thứ hạng, nên lọc bớt nhóm không làm các nhóm còn lại đổi màu.
"""
from contextlib import contextmanager
from contextvars import ContextVar

_dark: ContextVar[bool | None] = ContextVar("dark", default=None)
FONT = "'Be Vietnam Pro', ui-sans-serif, system-ui, sans-serif"

# Màu xám cùng tông lạnh với giao diện (dashboard/web/src/index.css); màu dữ liệu giữ nguyên.
_LIGHT = {
    "surface": "#ffffff", "ink": "#171a20", "ink2": "#505662", "muted": "#646a76",
    "neutral": "#e8eaee", "deemph": "#c4c8d0", "accent": "#2a78d6",
    "cat": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "seq": ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
    "pair": ("#86b6ef", "#1c5cab"),
    "on_strong": "#ffffff", "on_weak": "#171a20",
}
_DARK = {
    "surface": "#151922", "ink": "#e9eaec", "ink2": "#b4b9c3", "muted": "#8d93a0",
    "neutral": "#262b35", "deemph": "#4a5160", "accent": "#3987e5",
    "cat": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
    "seq": ["#0d366b", "#184f95", "#2a78d6", "#6da7ec", "#cde2fb"],
    "pair": ("#184f95", "#86b6ef"),
    "on_strong": "#0e1116", "on_weak": "#e9eaec",
}

# Màu khung box vẽ lên ảnh (cố định cả hai chế độ vì nền là ảnh).
BOX_ISSUE = "#f0efec"
BOX_SUBMITTED = "#eb6834"
BOX_TRUTH = "#2a78d6"
BOX_PROPOSED = "#1baf7a"
BOX_FINAL = "#eda100"


@contextmanager
def using(dark: bool):
    """Vẽ biểu đồ theo chế độ này trong khối `with`, bất kể giao diện nào gọi."""
    token = _dark.set(dark)
    try:
        yield
    finally:
        _dark.reset(token)


def is_dark() -> bool:
    if _dark.get() is not None:
        return _dark.get()
    try:  # bản Streamlit; bỏ khi bỏ hẳn Streamlit
        import streamlit as st
        return st.context.theme.type == "dark"
    except Exception:
        return False


def tokens() -> dict:
    return _DARK if is_dark() else _LIGHT


def vega_config() -> dict:
    """Màu chữ, lưới và phông cho spec Vega-Lite gửi ra frontend.

    Streamlit tự áp theme của nó lên biểu đồ; frontend thì không, nên spec phải mang theo cấu hình này.
    """
    t = tokens()
    text = dict(labelColor=t["ink2"], titleColor=t["muted"], labelFont=FONT, titleFont=FONT,
                labelFontSize=12, titleFontSize=12, titleFontWeight=500)
    return dict(
        background="transparent", font=FONT, view=dict(stroke=None),
        axis=dict(**text, gridColor=t["neutral"], domainColor=t["deemph"], tickColor=t["deemph"], titlePadding=10),
        legend=dict(**text, symbolType="circle"),
        text=dict(font=FONT, color=t["ink2"]),
    )


def ink_on(fill: str) -> str:
    """Màu chữ đặt trên một mảng màu: trắng hoặc đen tuỳ độ sáng của nền."""
    r, g, b = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r ** 2.2 + 0.7152 * g ** 2.2 + 0.0722 * b ** 2.2
    return "#0b0b0b" if lum > 0.24 else "#ffffff"
