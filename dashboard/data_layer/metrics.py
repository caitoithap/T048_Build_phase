"""Phép gộp nhỏ dùng chung cho các trang.

Các cờ KPI (lặp lại, thời gian xử lý, nguồn lỗi) đã nằm sẵn trong bảng; ở đây chỉ đếm
và chia theo bộ lọc đang chọn.
"""
from __future__ import annotations

import pandas as pd

import settings as S


def rate(issues: pd.DataFrame, workload: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Issue trên 100 vật đã review, theo các chiều `by`."""
    den = workload.groupby(by)["n_reviewed"].sum()
    num = issues.groupby(by).size().reindex(den.index, fill_value=0)
    out = pd.DataFrame({"n_issues": num, "n_reviewed": den}).reset_index()
    out["rate"] = out["n_issues"] / out["n_reviewed"] * 100
    out["low_n"] = out["n_reviewed"] < S.MIN_REVIEWED
    return out


def rate_matrix(issues: pd.DataFrame, workload: pd.DataFrame, row: str, col: str, cols: list[str]) -> pd.DataFrame:
    """Lưới `row` x `col`: mẫu số là số vật đã review của cả hàng."""
    den = workload.groupby(row)["n_reviewed"].sum()
    grid = pd.MultiIndex.from_product([den.index, cols], names=[row, col])
    out = issues.groupby([row, col]).size().reindex(grid, fill_value=0).rename("n_issues").reset_index()
    out["n_reviewed"] = out[row].map(den)
    out["rate"] = out["n_issues"] / out["n_reviewed"] * 100
    out["low_n"] = out["n_reviewed"] < S.MIN_REVIEWED
    return out
