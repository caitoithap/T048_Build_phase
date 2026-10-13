"""Đổi giữa bảng theo hợp đồng (dùng mã) và bảng cho giao diện (dùng nhãn), kèm kiểm tra giá trị.

`decode` là cửa duy nhất mọi bảng phải đi qua trước khi tới các trang, kể cả bảng giả.
Nhờ vậy bảng giả và bảng thật chạy cùng một đường, và lỗi ở hợp đồng lộ ra ngay ở chế độ giả.
"""
from __future__ import annotations

import pandas as pd

import settings as S
from data_layer import schema

_TRUE = {"true", "1", "1.0", "t", "yes", "y"}
_FALSE = {"false", "0", "0.0", "f", "no", "n"}
_TO_BOOL = {**dict.fromkeys(_TRUE, True), **dict.fromkeys(_FALSE, False)}
_TIME_COLS = ("created_at", "resolved_at")


def encode(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Bảng dùng nhãn -> bảng theo hợp đồng: chỉ giữ cột trong hợp đồng, đổi nhãn sang mã."""
    spec = schema.TABLES[name]
    out = df[[c for c in spec["columns"] if c in df.columns]].copy()
    for col, vocab in spec.get("enums", {}).items():
        if col not in out:
            continue
        to_code = {label: code for code, label in S.VOCAB[vocab].items()}
        strange = sorted({str(v) for v in out[col].dropna().unique() if v not in to_code})
        if strange:
            raise ValueError(f"Bảng {name}, cột {col}: nhãn không có trong settings.py: {strange}")
        out[col] = out[col].map(to_code)
    return out


def _as_bool(series: pd.Series) -> tuple[pd.Series | None, list[str]]:
    """Đưa cột đúng/sai về kiểu bool. Trả về (cột, các giá trị không hiểu được)."""
    if series.dtype == bool:
        return series, []
    text = series.astype("string").str.strip().str.lower()
    mapped = text.map(_TO_BOOL)
    strange = sorted(text[mapped.isna() & text.notna()].unique())
    if strange:
        return None, strange
    return (mapped.astype("boolean") if mapped.isna().any() else mapped.astype(bool)), []


def decode(name: str, raw: pd.DataFrame) -> tuple[pd.DataFrame | None, list[str], str | None]:
    """Bảng theo hợp đồng -> bảng cho giao diện.

    Trả về (bảng, các cột tuỳ chọn còn thiếu, lý do bị từ chối). Bảng bị từ chối thì là None.
    Cột tuỳ chọn còn thiếu được thêm vào dưới dạng cột trống, để trang nào lỡ đọc cũng không vỡ;
    trang phải hỏi `Tables.has(...)` trước khi dùng các cột này.
    """
    spec = schema.TABLES[name]
    optional = spec.get("optional", {})
    needed = schema.required(name)
    lacking = [c for c in needed if c not in raw.columns]
    if lacking:
        return None, [], "thiếu cột bắt buộc: " + ", ".join(lacking)
    df = raw.copy()

    for col in spec.get("bools", []):
        if col not in df:
            continue
        fixed, strange = _as_bool(df[col])
        if strange:
            return None, [], f"cột đúng/sai `{col}` có giá trị không hiểu được: {', '.join(strange[:5])}"
        if col in needed and fixed.isna().any():
            return None, [], f"cột bắt buộc `{col}` có ô trống"
        df[col] = fixed

    for col, vocab in spec.get("enums", {}).items():
        if col not in df:
            continue
        labels = S.VOCAB[vocab]
        strange = sorted({str(v) for v in df[col].dropna().unique() if v not in labels})
        if strange:
            more = f" và {len(strange) - 5} giá trị khác" if len(strange) > 5 else ""
            return None, [], (f"cột `{col}` có giá trị lạ: {', '.join(strange[:5])}{more}. "
                              f"Mã hợp lệ: {', '.join(labels)}")
        if col in needed and df[col].isna().any():
            return None, [], f"cột bắt buộc `{col}` có ô trống"
        df[col] = df[col].map(labels)

    for col in _TIME_COLS:
        if col in df and col in spec["columns"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if name == "issues":
        df["error_group"] = df["error_type"].map(S.TYPE_TO_GROUP)
        if "resolution_hours" not in df and "resolved_at" in df:
            df["resolution_hours"] = (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600

    missing = [c for c in optional if c not in df.columns]
    for col in missing:
        df[col] = pd.NA
    return df, missing, None
