import os
import sys
import site
import ctypes

# Fix Windows DLL WinError 1114 (Explicit C++ DLL Preloading for PyTorch on Windows)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

if sys.platform == "win32":
    site_dirs = site.getsitepackages() + [site.getusersitepackages()]
    for sp in site_dirs:
        t_lib = os.path.join(sp, "torch", "lib")
        if os.path.exists(t_lib):
            try:
                os.add_dll_directory(t_lib)
                for dll_name in ["libiomp5md.dll", "c10.dll", "torch_cpu.dll", "torch_python.dll"]:
                    dll_p = os.path.join(t_lib, dll_name)
                    if os.path.exists(dll_p):
                        try:
                            ctypes.CDLL(dll_p)
                        except Exception:
                            pass
            except Exception:
                pass

import time
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

import config

class YOLOCPUDetector:
    """
    YOLO Nano Inference & ByteTrack Tracking Engine optimized for CPU execution.
    """
    def __init__(self, model_name=config.DEFAULT_MODEL, conf_thresh=config.DEFAULT_CONF_THRESHOLD):
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        print(f"⚡ Loading YOLO Model [{model_name}] on CPU...")
        start_t = time.time()
        self.model = YOLO(model_name)
        load_t = round(time.time() - start_t, 2)
        print(f"✅ Model loaded successfully in {load_t}s!")

    def process_source(self, source_path, conf_thresh=None, min_box_size=config.DEFAULT_MIN_BOX_SIZE):
        """
        Process images or video from source_path using ByteTrack on CPU.
        Returns:
            list of dicts containing detection metadata and bounding boxes.
            dict with execution summary statistics (latency, count).
        """
        conf_thresh = conf_thresh or self.conf_thresh
        source_path = str(source_path)
        
        print(f"🔍 Running CPU Tracking on source: {source_path}")
        start_t = time.time()
        
        # Run ByteTrack tracking in CPU mode (with fallback to predict if tracker unavailable)
        try:
            results = self.model.track(
                source=source_path,
                tracker="bytetrack.yaml",
                conf=conf_thresh,
                device="cpu",
                stream=True,
                verbose=False
            )
        except Exception as e:
            print(f"⚠️ Tracking warning: {e}. Falling back to standard YOLO predict...")
            results = self.model.predict(
                source=source_path,
                conf=conf_thresh,
                device="cpu",
                stream=True,
                verbose=False
            )

        all_detections = []
        frame_count = 0
        total_objects = 0
        
        for frame_idx, r in enumerate(results):
            frame_count += 1
            boxes = r.boxes
            img_h, img_w = r.orig_shape if hasattr(r, 'orig_shape') else (720, 1280)
            
            if boxes is None or len(boxes) == 0:
                continue

            for box_idx, box in enumerate(boxes):
                # Bounding box coordinates in xyxy format
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                x1, y1, x2, y2 = xyxy
                w = max(0.0, x2 - x1)
                h = max(0.0, y2 - y1)

                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = self.model.names[cls_id]

                # Optional target class filtering
                if config.TARGET_CLASSES and cls_name not in config.TARGET_CLASSES:
                    continue

                # Track ID (assigned by ByteTrack)
                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else -1

                # Extract frame filename if available from r.path
                actual_frame_name = Path(r.path).name if (hasattr(r, 'path') and r.path) else f"frame_{frame_idx:06d}.jpg"

                # Extract polygon segmentation masks if available (e.g. yolov8n-seg.pt)
                polygon_pts = None
                if hasattr(r, 'masks') and r.masks is not None and len(r.masks) > box_idx:
                    try:
                        poly_array = r.masks.xy[box_idx]
                        polygon_pts = [[round(float(pt[0]), 2), round(float(pt[1]), 2)] for pt in poly_array]
                    except Exception:
                        polygon_pts = None

                detection = {
                    "frame_idx": frame_idx,
                    "frame_name": actual_frame_name,
                    "track_id": track_id,
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "bbox": [round(x1, 2), round(y1, 2), round(w, 2), round(h, 2)], # [x, y, w, h]
                    "bbox_xyxy": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    "polygon": polygon_pts,
                    "confidence": round(conf, 4),
                    "img_width": img_w,
                    "img_height": img_h
                }
                all_detections.append(detection)
                total_objects += 1

        total_time = round(time.time() - start_t, 3)
        fps = round(frame_count / total_time, 1) if total_time > 0 else 0
        latency_ms = round((total_time / frame_count) * 1000, 2) if frame_count > 0 else 0

        summary = {
            "total_frames": frame_count,
            "total_objects": total_objects,
            "total_time_sec": total_time,
            "latency_ms_per_frame": latency_ms,
            "fps": fps,
            "device": "CPU"
        }

        print(f"📊 Summary: Processed {frame_count} frames, detected {total_objects} objects in {total_time}s ({latency_ms} ms/frame, {fps} FPS on CPU).")
        return all_detections, summary
