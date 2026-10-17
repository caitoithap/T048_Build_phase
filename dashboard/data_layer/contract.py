"""Mô tả hợp đồng dữ liệu cho người đọc: trạng thái từng bảng và cột của từng bảng."""
from __future__ import annotations

import pandas as pd

import settings as S
from data_layer import schema, store


def status(data: store.Tables) -> pd.DataFrame:
    rows = []
    for name, spec in schema.TABLES.items():
        note = data.problems.get(name, "")
        waiting = data.missing.get(name, [])
        if not note and waiting:
            # Gom cột còn thiếu theo chặng sinh ra nó: đọc là biết còn chờ chặng nào.
            per_stage = pd.Series([spec["optional"][c] for c in waiting]).value_counts(sort=False)
            note = "Còn chờ: " + ", ".join(f"{stage} ({n} cột)" for stage, n in per_stage.items())
        rows.append({
            "Bảng": name, "Nguồn": data.origin[name],
            "Số dòng": f"{len(data[name]):,}" if data.available(name) else "–",
            "Chặng sinh ra": spec["stage"], "Ghi chú": note or "Đủ cột",
        })
    return pd.DataFrame(rows)


def columns(name: str) -> pd.DataFrame:
    spec = schema.TABLES[name]
    optional, enums, bools = spec.get("optional", {}), spec.get("enums", {}), spec.get("bools", [])
    rows = []
    for col, meaning in spec["columns"].items():
        if col in enums:
            values = "Mã: " + ", ".join(S.VOCAB[enums[col]])
        else:
            values = "true / false (hoặc 1 / 0)" if col in bools else ""
        rows.append((col, "Tuỳ chọn · " + optional[col] if col in optional else "Bắt buộc", meaning, values))
    return pd.DataFrame(rows, columns=["Cột", "Khi nào cần", "Ý nghĩa", "Giá trị hợp lệ"])
