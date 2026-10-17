"""Các trang đã chuyển sang API.

`BUILDERS`: trang phân tích dựng bằng khối chung (api/blocks.py), phục vụ ở /api/pages/<path>.
Trang tra cứu có route riêng trong api/main.py vì cần tương tác riêng (chọn issue, tải file).
"""
from api.pages import overview

BUILDERS = {"tong-quan": overview.build}
CUSTOM = {"chi-tiet-issue", "nguon-du-lieu"}
PORTED = set(BUILDERS) | CUSTOM
