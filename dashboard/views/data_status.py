"""Nguồn dữ liệu: chế độ đang chạy, trạng thái từng bảng, bảng mã và hợp đồng cột."""
import pandas as pd
import streamlit as st

import catalog
import settings as S
from data_layer import contract, schema, store
from ui import components as ui

META = catalog.PAGES["nguon-du-lieu"]
ROW_PX = 35  # chiều cao một dòng, để bảng trạng thái hiện đủ không phải cuộn


def render():
    data = store.load()
    n_real = sum(origin == store.REAL for origin in data.origin.values())
    ui.kpi_row([
        ("Chế độ", "Dữ liệu " + data.mode.lower(), "Số thật và số giả không bao giờ trộn trên cùng một màn hình."),
        ("Bảng thật dùng được", f"{n_real}/{len(schema.TABLES)}", None),
        ("Bộ đáp án", "Có" if S.GT_XML.exists() else "Thiếu", "Dùng để sinh số giả và để hiện ảnh."),
    ])
    # Thư mục bảng thật có thể được trỏ ra ngoài project; khi đó hiện nguyên đường dẫn.
    inside = S.PROJECT_DIR in S.REAL_DIR.parents
    folder = S.REAL_DIR.relative_to(S.PROJECT_DIR).as_posix() if inside else str(S.REAL_DIR)
    st.caption(f"Thả bảng thật vào `{folder}/` với tên `<tên bảng>.csv` hoặc `.parquet`. Chỉ cần một file là "
               "dashboard chuyển sang chế độ thật; bảng nào chưa có thì các trang ghi rõ còn chờ gì.")
    if data.mode == store.MOCK and data.has_real_files:
        st.info("Đang xem bằng dữ liệu giả theo công tắc ở thanh bên. Các file thật đang bị bỏ qua.",
                icon=":material/science:")
    if data.mode == store.REAL:
        for name, problem in data.problems.items():
            if not problem.startswith("chưa có file"):
                st.warning(f"Bảng `{name}` bị từ chối: {problem}.", icon=":material/warning:")

    status = contract.status(data)
    ui.table("Trạng thái từng bảng", status, height=ROW_PX * (len(status) + 1) + 3,
             note="Bảng chỉ cần đủ cột bắt buộc là được nhận. Cột tuỳ chọn bổ sung dần theo từng chặng.",
             column_config={"Bảng": st.column_config.TextColumn("Bảng", width="medium"),
                            "Nguồn": st.column_config.TextColumn("Nguồn", width="small"),
                            "Số dòng": st.column_config.TextColumn("Số dòng", width="small"),
                            "Chặng sinh ra": st.column_config.TextColumn("Chặng sinh ra", width="medium"),
                            "Ghi chú": st.column_config.TextColumn("Ghi chú", width="large")})

    st.subheader("File mẫu", anchor=False)
    st.caption("12 bảng giả ở đúng dạng hợp đồng: đúng tên cột và dùng mã. Dùng làm mẫu khi viết phần xuất của pipeline.")
    if S.GT_XML.exists():
        st.download_button("Tải bộ CSV mẫu", store.sample_zip(), "m22_bang_mau.zip", "application/zip",
                           icon=":material/download:")
    else:
        st.caption("Cần bộ đáp án để sinh file mẫu.")

    st.subheader("Bảng mã", anchor=False)
    st.caption("Dữ liệu ghi theo mã ở cột trái; giao diện hiện nhãn ở cột phải. Giá trị ngoài bảng mã làm cả bảng "
               "bị từ chối, kèm thông báo nêu đúng giá trị lạ. Đổi nhãn thì sửa ở settings.py; mã giữ nguyên.")
    for vocab, labels in S.VOCAB.items():
        if vocab == "class":
            st.markdown("**class**: " + ", ".join(f"`{c}`" for c in labels))
            continue
        with st.expander(f"{vocab} · {len(labels)} mã"):
            st.dataframe(pd.DataFrame(labels.items(), columns=["Mã trong dữ liệu", "Nhãn trên giao diện"]),
                         hide_index=True, width="stretch")

    st.subheader("Hợp đồng cột", anchor=False)
    st.caption("Cột ghi \"cần đáp án\" chỉ tính được khi có ground truth.")
    for name, spec in schema.TABLES.items():
        n_required = len(schema.required(name))
        with st.expander(f"{name} · {spec['title']} · {n_required} cột bắt buộc, "
                         f"{len(spec['columns']) - n_required} tuỳ chọn"):
            st.write(spec["desc"])
            st.dataframe(contract.columns(name), hide_index=True, width="stretch")
