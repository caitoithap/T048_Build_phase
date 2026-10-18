import config

class QCFilter:
    """
    Rule-based Quality Control Filter for pre-annotation bounding boxes.
    Filters out noisy, tiny, extreme aspect ratio, and low-confidence boxes.
    """
    def __init__(
        self,
        min_box_size=config.DEFAULT_MIN_BOX_SIZE,
        max_aspect_ratio=config.DEFAULT_MAX_BOX_ASPECT_RATIO,
        conf_thresh=config.DEFAULT_CONF_THRESHOLD
    ):
        self.min_box_size = min_box_size
        self.max_aspect_ratio = max_aspect_ratio
        self.conf_thresh = conf_thresh

    def apply_qc(self, detections):
        """
        Apply rule-based quality checks on raw detection results.
        Returns:
            kept_detections (list): Valid detections passing all QC rules.
            rejected_detections (list): Rejected detections with reason tags.
            qc_stats (dict): Summary metrics of filtered out noise.
        """
        kept = []
        rejected = []
        reasons_counter = {
            "too_small": 0,
            "extreme_aspect_ratio": 0,
            "low_confidence": 0,
            "out_of_bounds": 0
        }

        for det in detections:
            x, y, w, h = det["bbox"]
            img_w = det.get("img_width", 1280)
            img_h = det.get("img_height", 720)
            conf = det["confidence"]

            # Rule 1: Confidence Threshold Check
            if conf < self.conf_thresh:
                reasons_counter["low_confidence"] += 1
                det_copy = det.copy()
                det_copy["qc_reject_reason"] = "low_confidence"
                rejected.append(det_copy)
                continue

            # Rule 2: Minimum Box Dimension Check (w or h < min_size)
            if w < self.min_box_size or h < self.min_box_size:
                reasons_counter["too_small"] += 1
                det_copy = det.copy()
                det_copy["qc_reject_reason"] = "too_small"
                rejected.append(det_copy)
                continue

            # Rule 3: Extreme Aspect Ratio Check
            aspect_ratio = max(w / max(h, 1.0), h / max(w, 1.0))
            if aspect_ratio > self.max_aspect_ratio:
                reasons_counter["extreme_aspect_ratio"] += 1
                det_copy = det.copy()
                det_copy["qc_reject_reason"] = "extreme_aspect_ratio"
                rejected.append(det_copy)
                continue

            # Rule 4: Out-of-bounds / Invalid Coordinates Check
            if x < 0 or y < 0 or (x + w) > (img_w + 5) or (y + h) > (img_h + 5):
                reasons_counter["out_of_bounds"] += 1
                det_copy = det.copy()
                det_copy["qc_reject_reason"] = "out_of_bounds"
                rejected.append(det_copy)
                continue

            kept.append(det)

        total_input = len(detections)
        total_kept = len(kept)
        total_rejected = len(rejected)
        filter_rate_pct = round((total_rejected / total_input * 100), 2) if total_input > 0 else 0.0

        qc_stats = {
            "total_input_boxes": total_input,
            "kept_valid_boxes": total_kept,
            "rejected_boxes": total_rejected,
            "filter_rejection_rate_pct": filter_rate_pct,
            "reasons_breakdown": reasons_counter
        }

        print(f"🧹 QC Filter Applied: Kept {total_kept}/{total_input} boxes ({filter_rate_pct}% noise filtered out).")
        return kept, rejected, qc_stats
