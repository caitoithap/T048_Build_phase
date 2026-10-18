import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

class CVATExporter:
    """
    Exports bounding boxes and tracking IDs into CVAT XML (v1.1) and COCO JSON formats.
    """

    @staticmethod
    def export_to_cvat_xml(detections, output_path, image_name_map=None):
        """
        Exports detections to CVAT for Images 1.1 XML format.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        annotations = ET.Element("annotations")
        version = ET.SubElement(annotations, "version")
        version.text = "1.1"

        # Meta section
        meta = ET.SubElement(annotations, "meta")
        task = ET.SubElement(meta, "task")
        name = ET.SubElement(task, "name")
        name.text = "YOLO_Prelabel_Task"

        # Group detections by frame_idx
        frame_dict = {}
        for det in detections:
            f_idx = det["frame_idx"]
            if f_idx not in frame_dict:
                frame_dict[f_idx] = []
            frame_dict[f_idx].append(det)

        for f_idx in sorted(frame_dict.keys()):
            dets = frame_dict[f_idx]
            first_det = dets[0]
            img_name = first_det.get("frame_name", f"frame_{f_idx:06d}.jpg")
            if image_name_map and f_idx in image_name_map:
                img_name = image_name_map[f_idx]

            img_w = str(first_det.get("img_width", 1280))
            img_h = str(first_det.get("img_height", 720))

            image_elem = ET.SubElement(annotations, "image", {
                "id": str(f_idx),
                "name": img_name,
                "width": img_w,
                "height": img_h
            })

            for det in dets:
                x1, y1, w, h = det["bbox"]
                x2 = x1 + w
                y2 = y1 + h

                # If polygon points exist, export as polygon element
                if det.get("polygon"):
                    pts_str = ";".join([f"{pt[0]:.2f},{pt[1]:.2f}" for pt in det["polygon"]])
                    elem = ET.SubElement(image_elem, "polygon", {
                        "label": det["class_name"],
                        "occluded": "0",
                        "source": "auto-yolo-seg",
                        "points": pts_str,
                        "z_order": "0"
                    })
                else:
                    elem = ET.SubElement(image_elem, "box", {
                        "label": det["class_name"],
                        "occluded": "0",
                        "source": "auto-yolo",
                        "xtl": f"{x1:.2f}",
                        "ytl": f"{y1:.2f}",
                        "xbr": f"{x2:.2f}",
                        "ybr": f"{y2:.2f}",
                        "z_order": "0"
                    })

                # Attach track ID if present
                if det.get("track_id", -1) != -1:
                    attr_track = ET.SubElement(elem, "attribute", {"name": "track_id"})
                    attr_track.text = str(det["track_id"])

                attr_conf = ET.SubElement(elem, "attribute", {"name": "confidence"})
                attr_conf.text = f"{det['confidence']:.4f}"

        # Pretty format XML
        xml_bytes = ET.tostring(annotations, encoding="utf-8")
        parsed_xml = minidom.parseString(xml_bytes)
        pretty_xml = parsed_xml.toprettyxml(indent="  ")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        print(f"💾 CVAT XML 1.1 Exported: {output_path}")
        return str(output_path)

    @staticmethod
    def export_to_coco_json(detections, output_path):
        """
        Exports detections to COCO JSON format.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        categories_map = {}
        images_map = {}
        annotations_list = []

        ann_id = 1
        cat_id_counter = 1

        for det in detections:
            cls_name = det["class_name"]
            if cls_name not in categories_map:
                categories_map[cls_name] = cat_id_counter
                cat_id_counter += 1

            f_idx = det["frame_idx"]
            if f_idx not in images_map:
                images_map[f_idx] = {
                    "id": f_idx + 1,
                    "file_name": det.get("frame_name", f"frame_{f_idx:06d}.jpg"),
                    "width": det.get("img_width", 1280),
                    "height": det.get("img_height", 720)
                }

            cat_id = categories_map[cls_name]
            image_id = images_map[f_idx]["id"]
            x, y, w, h = det["bbox"]

            annotations_list.append({
                "id": ann_id,
                "image_id": image_id,
                "category_id": cat_id,
                "bbox": [x, y, w, h],
                "area": round(w * h, 2),
                "iscrowd": 0,
                "score": det["confidence"],
                "attributes": {
                    "track_id": det.get("track_id", -1)
                }
            })
            ann_id += 1

        coco_data = {
            "info": {
                "description": "YOLO Nano Pre-Annotation Export",
                "version": "1.0"
            },
            "images": list(images_map.values()),
            "categories": [{"id": cid, "name": cname} for cname, cid in categories_map.items()],
            "annotations": annotations_list
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(coco_data, f, indent=2)

        print(f"💾 COCO JSON Exported: {output_path}")
        return str(output_path)
