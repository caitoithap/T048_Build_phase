"""Màu dùng chung cho biểu đồ, chọn theo chế độ sáng hoặc tối của Streamlit.

Thứ tự màu phân loại là cố định (đã qua kiểm tra mù màu); màu đi theo tên nhóm,
không đi theo thứ hạng, nên lọc bớt nhóm không làm các nhóm còn lại đổi màu.
"""
import streamlit as st

_LIGHT = {
    "surface": "#ffffff", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
    "neutral": "#ecebe7", "deemph": "#c3c2b7", "accent": "#2a78d6",
    "cat": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"],
    "seq": ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
    "pair": ("#86b6ef", "#1c5cab"),
    "on_strong": "#ffffff", "on_weak": "#0b0b0b",
}
_DARK = {
    "surface": "#0e1117", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781",
    "neutral": "#2c2c2a", "deemph": "#52514e", "accent": "#3987e5",
    "cat": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
    "seq": ["#0d366b", "#184f95", "#2a78d6", "#6da7ec", "#cde2fb"],
    "pair": ("#184f95", "#86b6ef"),
    "on_strong": "#0b0b0b", "on_weak": "#f0efec",
}

# Màu khung box vẽ lên ảnh (cố định cả hai chế độ vì nền là ảnh).
BOX_ISSUE = "#f0efec"
BOX_SUBMITTED = "#eb6834"
BOX_TRUTH = "#2a78d6"
BOX_PROPOSED = "#1baf7a"
BOX_FINAL = "#eda100"


def is_dark() -> bool:
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


def tokens() -> dict:
    return _DARK if is_dark() else _LIGHT


def ink_on(fill: str) -> str:
    """Màu chữ đặt trên một mảng màu: trắng hoặc đen tuỳ độ sáng của nền."""
    r, g, b = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lum = 0.2126 * r ** 2.2 + 0.7152 * g ** 2.2 + 0.0722 * b ** 2.2
    return "#0b0b0b" if lum > 0.24 else "#ffffff"
