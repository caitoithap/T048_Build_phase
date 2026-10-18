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
