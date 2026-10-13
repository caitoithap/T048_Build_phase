"""Đọc ảnh thẳng từ file zip và vẽ box lên vùng cắt quanh vật."""
from __future__ import annotations

import io
import zipfile

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

import settings as S

Box = tuple[float, float, float, float]


@st.cache_data(max_entries=64, show_spinner=False)
def _raw(name: str) -> bytes | None:
    if not S.IMAGES_ZIP.exists():
        return None
    with zipfile.ZipFile(S.IMAGES_ZIP) as archive:
        try:
            return archive.read(name)
        except KeyError:
            return None


def box_of(row, prefix: str) -> Box | None:
    """Lấy box từ bốn cột <prefix>x1, y1, x2, y2; None nếu thiếu."""
    values = [row.get(f"{prefix}{k}") for k in ("x1", "y1", "x2", "y2")]
    return None if any(pd.isna(v) for v in values) else tuple(float(v) for v in values)


def crop(name: str, boxes: list[tuple[Box | None, str]], frame: list[Box | None] | None = None,
         min_width: int = 520) -> Image.Image | None:
    """Cắt vùng quanh các box rồi vẽ khung. `frame`: các box quyết định vùng cắt.

    Truyền cùng một `frame` cho nhiều ảnh để chúng cắt đúng một vùng và so được với nhau.
    """
    raw = _raw(name)
    if raw is None:
        return None
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    anchors = [b for b in (frame if frame is not None else [b for b, _ in boxes]) if b is not None]
    if anchors:
        x1, y1 = min(b[0] for b in anchors), min(b[1] for b in anchors)
        x2, y2 = max(b[2] for b in anchors), max(b[3] for b in anchors)
        margin = max(70.0, 1.2 * max(x2 - x1, y2 - y1))
        left, top = max(0, int(x1 - margin)), max(0, int(y1 - margin))
        right, bottom = min(img.width, int(x2 + margin)), min(img.height, int(y2 + margin))
    else:
        left, top, right, bottom = 0, 0, img.width, img.height
    out = img.crop((left, top, right, bottom))
    scale = min(6.0, max(1.0, min_width / out.width))
    if scale > 1:
        out = out.resize((round(out.width * scale), round(out.height * scale)), Image.LANCZOS)

    draw = ImageDraw.Draw(out)
    for box, color in boxes:
        if box is None:
            continue
        xs = sorted(((box[0] - left) * scale, (box[2] - left) * scale))
        ys = sorted(((box[1] - top) * scale, (box[3] - top) * scale))
        draw.rectangle([xs[0], ys[0], xs[1], ys[1]], outline=color, width=3)
    return out
