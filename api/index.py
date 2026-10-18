"""Vercel Python Function: bọc app FastAPI của dashboard M22.

Mọi request /api/* được vercel.json rewrite về đây. Code dashboard import theo kiểu
`import settings`, `from api.pages import ...` (chạy từ thư mục dashboard/), nên cần đưa
dashboard/ lên đầu sys.path trước khi import.
"""
import sys
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard"
sys.path.insert(0, str(DASHBOARD))
# Thư mục api/ ở gốc repo (chứa chính file này) trùng tên với package dashboard/api.
# Bỏ module "api" lỡ được nạp từ gốc, để import bên dưới lấy đúng dashboard/api.
sys.modules.pop("api", None)

from api.main import app  # noqa: E402  (Vercel tìm biến ASGI tên `app`)
