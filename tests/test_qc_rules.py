"""Test suite cho động cơ luật QC Rule Engine (src/qc_rules.py)."""
import pytest
from src.qc_rules import QCRuleEngine

def test_calculate_iou_identical():
    # 2 box trùng khít nhau [x, y, w, h]
    b1 = [10.0, 10.0, 50.0, 50.0]
    b2 = [10.0, 10.0, 50.0, 50.0]
    iou = QCRuleEngine.calculate_iou(b1, b2)
    assert pytest.approx(iou, 0.001) == 1.0

def test_calculate_iou_no_overlap():
    # 2 box tách rời nhau
    b1 = [0.0, 0.0, 10.0, 10.0]
    b2 = [20.0, 20.0, 10.0, 10.0]
    iou = QCRuleEngine.calculate_iou(b1, b2)
    assert iou == 0.0

def test_calculate_iou_partial_overlap():
    # 2 box diện tích 100, giao 50 -> union = 150 -> IoU = 50/150 = 1/3
    b1 = [0.0, 0.0, 10.0, 10.0]
    b2 = [5.0, 0.0, 10.0, 10.0]
    iou = QCRuleEngine.calculate_iou(b1, b2)
    assert pytest.approx(iou, 0.01) == 1.0 / 3.0

def test_rule_qc_out_of_bounds():
    engine = QCRuleEngine(min_size=15.0, max_aspect_ratio=6.5)
    bad_box = [{
        "frame_name": "frame_001.jpg",
        "class_name": "car",
        "bbox": [-5.0, 10.0, 50.0, 50.0],
        "img_width": 1280,
        "img_height": 720
    }]
    passed, errors, stats = engine.audit_annotations(bad_box)
    assert len(errors) == 1
    assert errors[0]["error_type"] == "OUT_OF_BOUNDS"
    assert len(passed) == 0

def test_rule_qc_too_small():
    engine = QCRuleEngine(min_size=15.0, max_aspect_ratio=6.5)
    tiny_box = [{
        "frame_name": "frame_001.jpg",
        "class_name": "car",
        "bbox": [10.0, 10.0, 10.0, 50.0],  # w = 10 < 15
        "img_width": 1280,
        "img_height": 720
    }]
    passed, errors, stats = engine.audit_annotations(tiny_box)
    assert len(errors) == 1
    assert errors[0]["error_type"] == "TOO_SMALL"
    assert len(passed) == 0

def test_rule_qc_extreme_aspect_ratio():
    engine = QCRuleEngine(min_size=15.0, max_aspect_ratio=6.5)
    skinny_box = [{
        "frame_name": "frame_001.jpg",
        "class_name": "person",
        "bbox": [100.0, 100.0, 15.0, 120.0],  # 120 / 15 = 8.0 > 6.5
        "img_width": 1280,
        "img_height": 720
    }]
    passed, errors, stats = engine.audit_annotations(skinny_box)
    assert len(errors) == 1
    assert errors[0]["error_type"] == "EXTREME_ASPECT_RATIO"

def test_rule_qc_duplicate_bbox():
    engine = QCRuleEngine(min_size=15.0, max_aspect_ratio=6.5, dup_iou=0.85)
    duplicate_boxes = [
        {
            "frame_name": "frame_001.jpg",
            "class_name": "car",
            "bbox": [100.0, 100.0, 80.0, 60.0],
            "img_width": 1280,
            "img_height": 720
        },
        {
            "frame_name": "frame_001.jpg",
            "class_name": "car",
            "bbox": [101.0, 101.0, 80.0, 60.0],  # IoU > 0.95
            "img_width": 1280,
            "img_height": 720
        }
    ]
    passed, errors, stats = engine.audit_annotations(duplicate_boxes)
    assert stats["error_breakdown"]["duplicate_bbox"] == 1
