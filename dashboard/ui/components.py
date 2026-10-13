"""Khung trang dùng chung: tiêu đề, bộ lọc, thẻ KPI, thẻ biểu đồ, và kiểm tra dữ liệu đã có chưa."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

import settings as S
from data_layer import schema, store
from ui import theme

_FILTER_NAMES = {"run": "Lần chạy", "class": "Class", "size": "Cỡ box", "annotator": "Annotator"}
_FILTER_KEYS = ("f_scope", "f_class", "f_size", "f_annotator", "f_hide_sign", "f_tables")
_CSS = "<style>.block-container{padding-top:2.4rem;padding-bottom:3rem}</style>"


@dataclass(frozen=True)
class Filters:
    runs: tuple = ()
    classes: tuple = ()
    sizes: tuple = ()
    annotators: tuple = ()
    hide_sign: bool = False
    show_tables: bool = False

    def apply(self, df: pd.DataFrame, runs: bool = True) -> pd.DataFrame:
        """Lọc theo những chiều mà bảng có cột tương ứng. `runs=False` để giữ mọi lần chạy."""
        keep = pd.Series(True, index=df.index)
        if runs and self.runs and "run" in df:
            keep &= df["run"].isin(self.runs)
        if "class_name" in df:
            if self.classes:
                keep &= df["class_name"].isin(self.classes)
            if self.hide_sign:
                keep &= df["class_name"] != "traffic sign"
        if self.sizes and "size_bucket" in df:
            keep &= df["size_bucket"].isin(self.sizes)
        if self.annotators:
            for col in ("annotator", "annotator_a", "annotator_b"):
                if col in df:
                    keep &= df[col].isin(self.annotators)
        return df[keep]


def keep_filter_state() -> None:
    """Giữ lựa chọn bộ lọc khi sang trang không vẽ hàng lọc.

    Streamlit xoá trạng thái của widget không được vẽ trong lượt chạy; gán lại giá trị
    cho chính nó là cách chính thức để giữ.
    """
    for key in _FILTER_KEYS:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


# ---------- dữ liệu đã có chưa ----------

def ready(data: store.Tables, title: str | None = None, **needs: list[str]) -> bool:
    """Kiểm tra các bảng và cột tuỳ chọn mà một phần giao diện cần.

    `needs`: tên bảng -> các cột tuỳ chọn cần có (danh sách rỗng nếu chỉ cần bảng tồn tại).
    Đủ thì trả True. Thiếu thì vẽ một thẻ nói rõ còn chờ gì và trả False; có `title` thì thẻ
    mang tiêu đề đó để giữ nguyên bố cục trang.
    """
    gaps = []
    for table, cols in needs.items():
        spec = schema.TABLES[table]
        if not data.available(table):
            gaps.append(f"Chưa dùng được bảng `{table}` ({spec['stage']}): {data.problems.get(table, 'không rõ')}.")
            continue
        lacking = [c for c in cols if c in data.missing.get(table, ())]
        if lacking:
            listed = ", ".join(f"`{c}` ({spec['optional'][c]})" for c in lacking)
            gaps.append(f"Bảng `{table}` chưa có cột {listed}.")
    if not gaps:
        return True
    message = " ".join(gaps)
    if title:
        with st.container(border=True, height="stretch"):
            st.markdown(f"**{title}**")
            st.caption(":material/hourglass_empty: Chưa có dữ liệu cho phần này. " + message)
    else:
        st.info("Trang này chưa có dữ liệu. " + message, icon=":material/hourglass_empty:")
    return False


def page_ready(meta: dict, data: store.Tables) -> bool:
    """Điều kiện tối thiểu để vẽ cả trang, khai báo ở META["requires"] của trang."""
    return ready(data, None, **meta.get("requires", {}))


# ---------- khung trang ----------

def page_header(meta: dict, data: store.Tables) -> None:
    st.html(_CSS)
    left, right = st.columns([4, 1.5], vertical_alignment="bottom")
    with left:
        st.header(meta["title"], anchor=False)
        st.caption(meta["question"])
    used = meta["tables"]
    absent = [t for t in used if not data.available(t)]
    with right.container(horizontal=True, horizontal_alignment="right"):
        if data.mode == store.MOCK:
            st.badge("Dữ liệu giả", icon=":material/science:", color="orange",
                     help="Mọi con số trên trang này là số tự sinh, không phải kết quả đo.")
        elif absent:
            st.badge(f"Dữ liệu thật · thiếu {len(absent)}/{len(used)} bảng", icon=":material/hourglass_empty:",
                     color="blue", help="Bảng chưa có: " + ", ".join(absent))
        else:
            st.badge("Dữ liệu thật", icon=":material/verified:", color="green")


def filter_bar(applicable: set[str], annotators: list[str]) -> Filters:
    """Một hàng lọc cho cả trang. Ô không áp dụng cho trang hiện tại bị khoá nhưng vẫn giữ lựa chọn."""
    off = {name: name not in applicable for name in _FILTER_NAMES}
    with st.container(border=True):
        c = st.columns([1.7, 1.7, 1.1, 1.3])
        scope = c[0].selectbox("Lần chạy", list(S.RUN_SCOPES), key="f_scope", disabled=off["run"],
                               help="Lô 2 chạy hai lần trên cùng ảnh, nên đối chứng và pilot không gộp chung.")
        classes = c[1].multiselect("Class", S.CLASSES, key="f_class", placeholder="Tất cả", disabled=off["class"])
        sizes = c[2].multiselect("Cỡ box", S.SIZES, key="f_size", placeholder="Tất cả", disabled=off["size"])
        people = c[3].multiselect("Annotator", annotators, key="f_annotator", placeholder="Tất cả",
                                  disabled=off["annotator"])
        with st.container(horizontal=True, gap="large"):
            hide_sign = st.toggle(
                "Ẩn traffic sign", key="f_hide_sign", disabled=off["class"],
                help="Model huấn luyện trên COCO gần như không có class này, nên nó lấn át các lỗi khác.")
            show_tables = st.toggle("Bảng số liệu", key="f_tables", help="Hiện bảng số ngay dưới mỗi biểu đồ.")
            skipped = [label for name, label in _FILTER_NAMES.items() if off[name]]
            if skipped:
                st.caption("Trang này không dùng bộ lọc: " + ", ".join(skipped) + ".")

    chosen = Filters(
        runs=() if off["run"] else S.RUN_SCOPES[scope],
        classes=() if off["class"] else tuple(classes),
        sizes=() if off["size"] else tuple(sizes),
        annotators=() if off["annotator"] else tuple(people),
        hide_sign=hide_sign and not off["class"],
        show_tables=show_tables,
    )
    st.session_state["_filters"] = chosen
    return chosen


def filters() -> Filters:
    return st.session_state.get("_filters", Filters())


def kpi_row(items: list[tuple[str, str | None, str | None]]) -> None:
    """Hàng thẻ KPI. Giá trị None nghĩa là chưa có dữ liệu để tính: hiện gạch ngang, không hiện số 0."""
    for col, (label, value, hint) in zip(st.columns(len(items)), items):
        if value is None:
            col.metric(label, "–", help="Chưa có dữ liệu cho chỉ số này. " + (hint or ""), border=True)
        else:
            col.metric(label, value, help=hint, border=True)


def chart(title: str, figure, note: str | None = None, table: pd.DataFrame | None = None) -> None:
    """Thẻ biểu đồ. Bảng số đi kèm hiện ra khi bật "Bảng số liệu"."""
    with st.container(border=True, height="stretch"):
        st.markdown(f"**{title}**")
        if note:
            st.caption(note)
        st.altair_chart(figure, width="stretch")
        if table is not None and filters().show_tables:
            st.dataframe(table, hide_index=True, width="stretch")


def table(title: str, df: pd.DataFrame, note: str | None = None, **kwargs) -> None:
    with st.container(border=True, height="stretch"):
        st.markdown(f"**{title}**")
        if note:
            st.caption(note)
        st.dataframe(df, hide_index=True, width="stretch", **kwargs)


def percent_column(label: str):
    """Cột thanh tiến độ 0–100%, dùng màu nhấn của biểu đồ thay cho màu đỏ mặc định."""
    return st.column_config.ProgressColumn(label, format="%.0f%%", min_value=0, max_value=100,
                                           color=theme.tokens()["accent"])


def empty(message: str = "Không có dữ liệu với bộ lọc hiện tại.") -> None:
    st.info(message, icon=":material/filter_alt_off:")


def simulated(message: str) -> None:
    """Ghi chú cho phần mà số liệu phụ thuộc vào dữ liệu mô phỏng."""
    st.info(message, icon=":material/science:")
