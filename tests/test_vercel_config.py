"""Test suite cho cấu hình triển khai Vercel (api/index.py, vercel.json, api/requirements.txt, .vercelignore)."""
import json
import runpy
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent

# File function và frontend cần có trên Vercel, và file của pipeline/Streamlit/VPS phải bị bỏ.
KEEP = ["dashboard/web/src/App.tsx", "dashboard/web/index.html", "dashboard/web/package-lock.json",
        "dashboard/api/main.py", "dashboard/settings.py", "dashboard/catalog.py", "dashboard/data_real/.gitkeep",
        "dashboard/app.py", "sample_data_output1/annotations.xml", "sample_data_output1/images.zip",
        "api/index.py", "api/requirements.txt", "vercel.json", ".python-version"]
DROP = ["src/qc_rules.py", "app.py", "cli.py", "config.py", "yolov8n.pt", "tests/test_cli.py",
        ".venv/bin/python", "deploy/deploy.sh"]


def test_vercel_entry_exposes_fastapi_app():
    app = runpy.run_path(str(BASE_DIR / "api" / "index.py"))["app"]
    assert isinstance(app, FastAPI)
    client = TestClient(app)
    assert client.get("/api/meta", params={"demo": True}).status_code == 200
    assert client.get("/api/pages/tong-quan", params={"demo": True}).status_code == 200


def test_vercel_json():
    config = json.loads((BASE_DIR / "vercel.json").read_text(encoding="utf-8"))
    function = config["functions"]["api/index.py"]
    assert "sample_data_output1/annotations.xml" in function["includeFiles"]
    assert "sample_data_output1/images.zip" in function["includeFiles"]
    assert config["rewrites"][0]["source"] == "/api/(.*)"
    assert config["outputDirectory"] == "dashboard/web/dist"


def test_api_requirements_stay_light():
    lines = (BASE_DIR / "api" / "requirements.txt").read_text(encoding="utf-8").lower().splitlines()
    packages = [line.split("#")[0].strip() for line in lines if line.split("#")[0].strip()]
    for heavy in ("torch", "ultralytics", "opencv", "pyarrow", "streamlit", "uvicorn"):
        assert not any(p.startswith(heavy) for p in packages), heavy


def test_vercelignore_keeps_build_inputs():
    pathspec = pytest.importorskip("pathspec")
    spec = pathspec.GitIgnoreSpec.from_lines((BASE_DIR / ".vercelignore").read_text(encoding="utf-8").splitlines())
    assert [p for p in KEEP if spec.match_file(p)] == []
    assert [p for p in DROP if not spec.match_file(p)] == []
