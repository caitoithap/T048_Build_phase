"""Test suite cho Data Layer (dashboard/data_layer: schema, store, metrics, codec)."""
import sys
from pathlib import Path
import pytest

# Thêm dashboard vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "dashboard"))

from data_layer import schema, store, metrics

def test_schema_tables_definition():
    assert len(schema.TABLES) == 12
    required_tables = [
        "issues", "workload", "review_assignments", "reviewer_overlap",
        "pair_agreement", "object_votes", "gt_scores", "image_scores",
        "patches", "recommendations", "annotators", "reviewers"
    ]
    for table_name in required_tables:
        assert table_name in schema.TABLES
        assert "columns" in schema.TABLES[table_name]
        req_cols = schema.required(table_name)
        assert len(req_cols) > 0

def test_store_load_mock_data():
    data = store.load()
    assert data is not None
    assert "issues" in data
    assert "workload" in data
    assert len(data["issues"]) > 0
    assert len(data["workload"]) > 0

def test_metrics_rate_calculation():
    data = store.load()
    issues = data["issues"]
    workload = data["workload"]
    
    rate_df = metrics.rate(issues, workload, ["class_name"])
    assert not rate_df.empty
    assert "class_name" in rate_df.columns
    assert "rate" in rate_df.columns
    assert "n_issues" in rate_df.columns
    assert "n_reviewed" in rate_df.columns
    assert (rate_df["rate"] >= 0).all()
