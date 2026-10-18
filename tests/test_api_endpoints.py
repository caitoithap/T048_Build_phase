"""Test suite cho FastAPI Backend API endpoints (dashboard/api/main.py)."""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "dashboard"))

from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_meta_endpoint(client):
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert "options" in data
    assert "mode" in data
    assert "n_tables" in data
    assert data["n_tables"] == 12

def test_api_page_overview_endpoint(client):
    response = client.get("/api/pages/tong-quan")
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert len(data["rows"]) > 0
    # Kiểm tra có khối KPI
    first_row_blocks = data["rows"][0]["blocks"]
    assert any(b["type"] == "kpis" for b in first_row_blocks)

def test_api_issues_endpoint(client):
    response = client.get("/api/issues")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "max_listed" in data
    assert "reviewers" in data

def test_api_data_status_endpoint(client):
    response = client.get("/api/data-status")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "status" in data
    assert "columns" in data["status"]
    assert "rows" in data["status"]
    assert len(data["status"]["rows"]) == 12

ANALYTICS_PAGES = ["tong-quan", "top-loi", "class-kho", "annotator", "cham-cheo-annotator",
                   "cham-cheo-reviewer", "sua-annotator", "sua-agent", "khuyen-nghi-pilot"]


@pytest.mark.parametrize("dark", [False, True])
@pytest.mark.parametrize("demo", [False, True])
@pytest.mark.parametrize("path", ANALYTICS_PAGES)
def test_api_analytics_pages(client, path, demo, dark):
    response = client.get(f"/api/pages/{path}", params={"demo": demo, "dark": dark})
    assert response.status_code == 200, response.text
    rows = response.json()["rows"]
    assert rows
    for row in rows:
        assert len(row["widths"]) == len(row["blocks"])
        assert all("type" in b for b in row["blocks"])


def test_api_meta_all_analytics_ported(client):
    pages = [p for s in client.get("/api/meta").json()["sections"] for p in s["pages"]]
    assert all(p["ported"] for p in pages)


def test_api_unknown_page_404(client):
    assert client.get("/api/pages/khong-co").status_code == 404
