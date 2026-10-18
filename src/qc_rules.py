import xml.etree.ElementTree as ET
import json
import math
from pathlib import Path
import numpy as np

import config

class QCRuleEngine:
    """
    Rule-based QC Engine for auditing computer vision annotations (CVAT XML, COCO JSON, YOLO TXT).
    Operates 100% on CPU without requiring GPU hardware.
    """
    def __init__(self, min_size=config.MIN_BBOX_SIZE_PX, max_aspect_ratio=config.MAX_ASPECT_RATIO, dup_iou=config.DUPLICATE_IOU_THRESH):
        self.min_size = min_size
        self.max_aspect_ratio = max_aspect_ratio
        self.dup_iou = dup_iou

    @staticmethod
    def calculate_iou(boxA, boxB):
        """
        Calculate Intersection over Union (IoU) between two bounding boxes [x, y, w, h].
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        inter_w = max(0.0, xB - xA)
        inter_h = max(0.0, yB - yA)
        inter_area = inter_w * inter_h

        boxA_area = boxA[2] * boxA[3]
        boxB_area = boxB[2] * boxB[3]
        union_area = boxA_area + boxB_area - inter_area

        if union_area <= 0:
            return 0.0
        return inter_area / union_area

    def parse_cvat_xml(self, xml_path):
        """
        Parses CVAT XML 1.1 file into structured annotations list.
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        parsed_data = []

        for img_elem in root.findall("image"):
            frame_id = int(img_elem.attrib.get("id", 0))
            frame_name = img_elem.attrib.get("name", f"frame_{frame_id:06d}.jpg")
            img_w = float(img_elem.attrib.get("width", 1280))
            img_h = float(img_elem.attrib.get("height", 720))

            # Parse Bboxes
            for box in img_elem.findall("box"):
                xtl = float(box.attrib.get("xtl", 0))
                ytl = float(box.attrib.get("ytl", 0))
                xbr = float(box.attrib.get("xbr", 0))
                ybr = float(box.attrib.get("ybr", 0))
                label = box.attrib.get("label", "unknown")
                w = max(0.0, xbr - xtl)
                h = max(0.0, ybr - ytl)

                parsed_data.append({
                    "frame_idx": frame_id,
                    "frame_name": frame_name,
                    "class_name": label,
                    "type": "box",
                    "bbox": [xtl, ytl, w, h],
                    "img_width": img_w,
                    "img_height": img_h
                })

            # Parse Polygons
            for poly in img_elem.findall("polygon"):
                label = poly.attrib.get("label", "unknown")
                pts_str = poly.attrib.get("points", "")
                pts = []
                if pts_str:
                    for pair in pts_str.split(";"):
                        coords = pair.split(",")
                        if len(coords) == 2:
                            pts.append([float(coords[0]), float(coords[1])])

                if pts:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    min_x, min_y, max_x, max_y = min(xs), min(ys), max(xs), max(ys)
                    parsed_data.append({
                        "frame_idx": frame_id,
                        "frame_name": frame_name,
                        "class_name": label,
                        "type": "polygon",
                        "bbox": [min_x, min_y, max_x - min_x, max_y - min_y],
                        "polygon": pts,
                        "img_width": img_w,
                        "img_height": img_h
                    })

        return parsed_data

    def audit_annotations(self, annotations):
        """
        Runs rule-based QC checks on annotations list.
        Returns:
            passed_annotations (list): Valid annotations passing QC.
            flagged_errors (list): Flagged annotation errors with error tags and details.
            rule_stats (dict): QC Error summary metrics.
        """
        passed = []
        errors = []
        counts = {
            "out_of_bounds": 0,
            "too_small": 0,
            "extreme_aspect_ratio": 0,
            "duplicate_bbox": 0
        }

        frame_groups = {}
        for ann in annotations:
            f_name = ann["frame_name"]
            if f_name not in frame_groups:
                frame_groups[f_name] = []
            frame_groups[f_name].append(ann)

        for f_name, anns in frame_groups.items():
            kept_in_frame = []
            for i, ann in enumerate(anns):
                x, y, w, h = ann["bbox"]
                img_w = ann.get("img_width", 1280)
                img_h = ann.get("img_height", 720)
                is_err = False

                # Check 1: Out of bounds
                if x < 0 or y < 0 or (x + w) > (img_w + 5) or (y + h) > (img_h + 5):
                    counts["out_of_bounds"] += 1
                    err_entry = ann.copy()
                    err_entry["error_type"] = "OUT_OF_BOUNDS"
                    err_entry["error_msg"] = f"Khung Bbox tràn ra ngoài viền ảnh ({x:.1f}, {y:.1f}, {w:.1f}, {h:.1f})"
                    errors.append(err_entry)
                    is_err = True

                # Check 2: Too small
                elif w < self.min_size or h < self.min_size:
                    counts["too_small"] += 1
                    err_entry = ann.copy()
                    err_entry["error_type"] = "TOO_SMALL"
                    err_entry["error_msg"] = f"Bbox rác quá nhỏ ({w:.1f}x{h:.1f}px < {self.min_size}px)"
                    errors.append(err_entry)
                    is_err = True

                # Check 3: Extreme aspect ratio
                elif max(w / max(h, 1.0), h / max(w, 1.0)) > self.max_aspect_ratio:
                    counts["extreme_aspect_ratio"] += 1
                    err_entry = ann.copy()
                    err_entry["error_type"] = "EXTREME_ASPECT_RATIO"
                    err_entry["error_msg"] = f"Tỷ lệ khung hình bất thường (w/h = {w/max(h,1.0):.1f})"
                    errors.append(err_entry)
                    is_err = True

                if not is_err:
                    kept_in_frame.append(ann)

            # Check 4: Duplicate Bboxes within frame
            for i in range(len(kept_in_frame)):
                for j in range(i + 1, len(kept_in_frame)):
                    b1 = kept_in_frame[i]
                    b2 = kept_in_frame[j]
                    if b1["class_name"] == b2["class_name"]:
                        iou = self.calculate_iou(b1["bbox"], b2["bbox"])
                        if iou > self.dup_iou:
                            counts["duplicate_bbox"] += 1
                            err_entry = b2.copy()
                            err_entry["error_type"] = "DUPLICATE_BBOX"
                            err_entry["error_msg"] = f"Bbox trùng lặp với Bbox khác (IoU = {iou:.2f} > {self.dup_iou})"
                            errors.append(err_entry)

            for ann in kept_in_frame:
                if ann not in errors:
                    passed.append(ann)

        rule_stats = {
            "total_audited_annotations": len(annotations),
            "valid_annotations_count": len(passed),
            "rule_errors_count": len(errors),
            "rule_error_rate_pct": round(len(errors) / len(annotations) * 100, 2) if len(annotations) > 0 else 0.0,
            "error_breakdown": counts
        }

        print(f"🧹 Rule QC Complete: Audited {len(annotations)} annotations, found {len(errors)} rule errors.")
        return passed, errors, rule_stats
