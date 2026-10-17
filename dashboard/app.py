"""M22 – CVAT Issue Analytics Dashboard (khung giao diện).

Chạy từ thư mục gốc của project:
    streamlit run dashboard/app.py --server.address localhost
"""
import streamlit as st

st.set_page_config(page_title="M22 · Issue Analytics", page_icon=":material/monitoring:", layout="wide")

import catalog  # noqa: E402
from data_layer import store  # noqa: E402
from ui import components as ui  # noqa: E402
from views import (  # noqa: E402
    annotators, classes, cross_annotators, cross_reviewers, data_status, fix_agent, fix_annotator,
    fix_recommendations, issue_detail, overview, top_errors,
)

VIEWS = {module.META["path"]: module for module in (
    annotators, classes, cross_annotators, cross_reviewers, data_status, fix_agent, fix_annotator,
    fix_recommendations, issue_detail, overview, top_errors,
)}

pages, meta_of = {}, {}
for section, paths in catalog.SECTIONS.items():
    pages[section] = []
    for path in paths:
        module = VIEWS[path]
        meta = module.META
        meta_of[meta["title"]] = meta
        pages[section].append(st.Page(module.render, title=meta["title"], icon=meta["icon"],
                                      url_path=meta["path"], default=module is overview))
current = st.navigation(pages)

try:
    data = store.load()
except FileNotFoundError as error:
    st.error(f"Không tìm thấy bộ đáp án để dựng dữ liệu giả: {error.filename}", icon=":material/error:")
    st.stop()

with st.sidebar:
    if data.mode == store.REAL:
        n_real = sum(origin == store.REAL for origin in data.origin.values())
        st.caption(f"Đang dùng dữ liệu thật: {n_real}/{len(data.origin)} bảng. Bảng chưa có thì để trống.")
    else:
        st.caption("Đang dùng dữ liệu giả cho mọi bảng.")
    if data.has_real_files:
        st.toggle("Xem bằng dữ liệu giả", key=store.DEMO_KEY,
                  help="Tạm bỏ qua các file thật để xem giao diện đầy đủ. Số thật và số giả không bao giờ trộn.")

meta = meta_of[current.title]
ui.keep_filter_state()
ui.page_header(meta, data)
if meta["filters"]:
    ui.filter_bar(meta["filters"], data.annotator_names())
if ui.page_ready(meta, data):
    current.run()
