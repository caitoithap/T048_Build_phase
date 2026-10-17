"""Bộ lọc dùng chung cho mọi trang, không phụ thuộc giao diện nào."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


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
