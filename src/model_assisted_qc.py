import os
from pathlib import Path
import numpy as np
from ultralytics import YOLO

import config
from src.qc_rules import QCRuleEngine

class ModelAssistedQCAuditor:
    """
    Model-assisted QC Engine running lightweight CPU model to detect missing objects and class mislabels.
    """
    def __init__(self, model_name=config.AUDIT_MODEL_NAME, conf_thresh=config.MODEL_ASSIST_CONF):
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        print(f"⚡ Loading Audit AI Model [{model_name}] on CPU...")
        self.model = YOLO(model_name)

    def audit_missing_and_mislabels(self, image_dir, human_annotations):
        """
        Compares human annotations against high-confidence AI predictions.
        Returns:
            flagged_missing_objects (list): High-confidence AI detections missed by human.
            flagged_class_mismatches (list): Bboxes where human and AI assign different classes.
        """
        image_dir = Path(image_dir)
        flagged_missing = []
        flagged_mismatch = []

        # Find images to audit
        sample_imgs = sorted(list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpeg")))
        if not sample_imgs:
            print("⚠️ No images found for model-assisted audit.")
            return flagged_missing, flagged_mismatch

        # Group human annotations by frame_name
        human_frame_map = {}
        for ann in human_annotations:
            fname = ann["frame_name"]
            if fname not in human_frame_map:
                human_frame_map[fname] = []
            human_frame_map[fname].append(ann)

        for img_p in sample_imgs:
            fname = img_p.name
            human_anns = human_frame_map.get(fname, [])

            # Run inference on CPU
            try:
                results = self.model.predict(source=str(img_p), conf=self.conf_thresh, device="cpu", verbose=False)
            except Exception as e:
                print(f"⚠️ Prediction error on {fname}: {e}")
                continue

            for r in results:
                if r.boxes is None or len(r.boxes) == 0:
                    continue

                for box in r.boxes:
                    ai_conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    ai_class = self.model.names[cls_id]

                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    x1, y1, x2, y2 = xyxy
                    w, h = max(0.0, x2 - x1), max(0.0, y2 - y1)
                    ai_box = [x1, y1, w, h]

                    # Compare with human boxes
                    matched_human = None
                    max_iou = 0.0
                    for h_ann in human_anns:
                        iou = QCRuleEngine.calculate_iou(ai_box, h_ann["bbox"])
                        if iou > max_iou:
                            max_iou = iou
                            matched_human = h_ann

                    # Flag 1: High confidence object missed by human (IoU < 0.3)
                    if max_iou < 0.3 and ai_conf >= self.conf_thresh:
                        flagged_missing.append({
                            "frame_name": fname,
                            "error_type": "MISSING_OBJECT",
                            "class_name": ai_class,
                            "bbox": [round(x1, 1), round(y1, 1), round(w, 1), round(h, 1)],
                            "confidence": round(ai_conf, 3),
                            "error_msg": f"AI phát hiện chắc chắn ({ai_conf*100:.0f}%) có [{ai_class}] nhưng người gán nhãn bỏ sót!"
                        })

                    # Flag 2: Class mismatch (IoU > 0.5 but different class)
                    elif max_iou >= 0.5 and matched_human and matched_human["class_name"] != ai_class:
                        flagged_mismatch.append({
                            "frame_name": fname,
                            "error_type": "CLASS_MISMATCH",
                            "human_class": matched_human["class_name"],
                            "ai_class": ai_class,
                            "bbox": matched_human["bbox"],
                            "confidence": round(ai_conf, 3),
                            "error_msg": f"Người gán nhãn dán '{matched_human['class_name']}' nhưng AI nghi ngờ là '{ai_class}'"
                        })

        print(f"🤖 Model-Assisted Audit Complete: Flagged {len(flagged_missing)} missing objects & {len(flagged_mismatch)} class mismatches.")
        return flagged_missing, flagged_mismatch
