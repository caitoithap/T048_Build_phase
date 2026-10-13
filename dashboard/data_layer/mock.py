"""Sinh dữ liệu giả cho dashboard M22 từ bộ đáp án BDD100K thật.

Mỗi vật trong đáp án được gán một kết quả cho từng annotator (đúng, bỏ sót, sai class,
lỗi box) theo xác suất phụ thuộc class, cỡ box và độ che khuất. Kết quả do chính file
này sinh ra nên không cần ghép box theo IoU. Pipeline thật thay các bảng này bằng file
trong `data_real/` (xem schema.py).

Mọi xác suất ở đây là tham số tự đặt để giao diện có số mà vẽ, không phải kết quả đo.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

import settings as S
from data_layer import codec

SEED = 22
JOBS_PER_BATCH = 4
FRAMES_REVIEWED = 8  # reviewer xem mẫu frame của mỗi job, không xem hết
BASE_TIME = pd.Timestamp("2026-09-21 08:00")

YOLO_COCO = "YOLO · COCO"
DETR_COCO = "DETR · COCO"
OPEN_VOCAB = "Từ vựng mở"

# box_mix = tỷ trọng (quá nhỏ, quá lớn); phần còn lại là lệch.
ANNOTATORS = [
    dict(annotator="A", model="yolov8n", family=YOLO_COCO, config="640px, ngưỡng thấp",
         miss=0.30, cls=0.05, box=0.10, extra=2.0, box_mix=(0.20, 0.55), fix_miss=0.0, fix_cls=0.0, fix_all=0.0),
    dict(annotator="B", model="yolov8n", family=YOLO_COCO, config="320px, ngưỡng cao",
         miss=0.48, cls=0.06, box=0.14, extra=0.3, box_mix=(0.55, 0.20), fix_miss=0.0, fix_cls=0.0, fix_all=0.0),
    dict(annotator="C", model="yolov8s", family=YOLO_COCO, config="640px, sửa 90% lỗi class, 30% lỗi sót",
         miss=0.26, cls=0.05, box=0.09, extra=0.8, box_mix=(0.30, 0.35), fix_miss=0.3, fix_cls=0.9, fix_all=0.0),
    dict(annotator="D", model="rtdetr-l", family=DETR_COCO, config="mặc định",
         miss=0.18, cls=0.04, box=0.07, extra=1.2, box_mix=(0.25, 0.45), fix_miss=0.0, fix_cls=0.0, fix_all=0.0),
    dict(annotator="E", model="yolov8m", family=YOLO_COCO, config="640px, sửa 80% mọi loại (đối chứng)",
         miss=0.22, cls=0.04, box=0.08, extra=0.7, box_mix=(0.30, 0.35), fix_miss=0.0, fix_cls=0.0, fix_all=0.8),
    dict(annotator="F", model="YOLO-World", family=OPEN_VOCAB, config="class lấy từ guideline",
         miss=0.30, cls=0.09, box=0.12, extra=1.4, box_mix=(0.30, 0.35), fix_miss=0.0, fix_cls=0.0, fix_all=0.0),
]
NAMES = [a["annotator"] for a in ANNOTATORS]
BY_NAME = {a["annotator"]: a for a in ANNOTATORS}

REVIEWERS = [
    dict(reviewer="R1", style="Khó tính", fa=0.040,
         catch={"Bỏ sót vật": 0.85, "Sai class": 0.90, "Lỗi box": 0.90, "Box thừa": 0.90, "Trùng lặp": 0.85}),
    dict(reviewer="R2", style="Trung bình", fa=0.020,
         catch={"Bỏ sót vật": 0.65, "Sai class": 0.80, "Lỗi box": 0.60, "Box thừa": 0.75, "Trùng lặp": 0.70}),
    dict(reviewer="R3", style="Dễ tính", fa=0.008,
         catch={"Bỏ sót vật": 0.45, "Sai class": 0.65, "Lỗi box": 0.30, "Box thừa": 0.60, "Trùng lặp": 0.50}),
]

CLS_MULT = {"car": 0.4, "person": 0.5, "traffic light": 0.3, "traffic sign": 0.5, "truck": 5.0,
            "bus": 4.0, "bike": 2.5, "motor": 3.0, "rider": 1.0, "train": 6.0}
CONFUSE = {"truck": ["car", "bus"], "bus": ["truck", "car"], "car": ["truck"], "bike": ["motor"],
           "motor": ["bike"], "person": ["rider"], "rider": ["person"], "traffic light": ["traffic sign"],
           "traffic sign": ["traffic light"], "train": ["bus"]}
FP_CLASSES = ["car", "person", "traffic light", "traffic sign", "truck"]
FP_PROBS = [0.35, 0.20, 0.20, 0.15, 0.10]

RESOLVE_MEDIAN_H = {"Bỏ sót vật": 20, "Lỗi box": 12, "Sai class": 6, "Trùng lặp": 4, "Box thừa": 5, "Mơ hồ": 40}
ACTION_OF = {"Bỏ sót vật": "Thêm box", "Lỗi box": "Chỉnh box", "Sai class": "Đổi class",
             "Trùng lặp": "Xoá box", "Box thừa": "Xoá box"}
# Khi annotator sửa khác yêu cầu thì thường làm một trong hai thao tác này.
OTHER_ACTION = {"Thêm box": ["Chỉnh box", "Đổi class"], "Xoá box": ["Chỉnh box", "Đổi class"],
                "Đổi class": ["Chỉnh box", "Xoá box"], "Chỉnh box": ["Đổi class", "Xoá box"]}
# Annotator phản hồi issue: (sửa đúng yêu cầu, sửa khác yêu cầu); phần còn lại là đóng mà không sửa.
RESPONSE = {"A": (0.70, 0.10), "B": (0.55, 0.15), "C": (0.85, 0.07),
            "D": (0.75, 0.10), "E": (0.90, 0.05), "F": (0.65, 0.15)}

# Cấu hình sau can thiệp, áp cho lần chạy pilot của lô 2.
PILOT_TWEAKS = {
    "miss_mult": {("A", "car"): 1.15},
    "miss_set": {("A", "traffic sign"): 0.50, ("D", "traffic sign"): 0.45},
    "extra_mult": {("A", "car"): 0.35, ("A", "traffic sign"): 6.0, ("D", "traffic sign"): 6.0},
    "cls_mult": {("F", "truck"): 0.35, ("F", "bus"): 0.35},
}
RECOMMENDATIONS = [
    dict(rec_id="KN-01", scope="A", error_group="Box thừa", class_name="car", attributed_source="Model",
         action="Nâng ngưỡng tin cậy của car từ 0.25 lên 0.40", status="Đã áp dụng", measurable=True,
         side_group="Bỏ sót vật"),
    dict(rec_id="KN-02", scope="A", error_group="Bỏ sót vật", class_name="traffic sign", attributed_source="Model",
         action="Ghép thêm model từ vựng mở cho traffic sign", status="Đã áp dụng", measurable=True,
         side_group="Box thừa"),
    dict(rec_id="KN-03", scope="D", error_group="Bỏ sót vật", class_name="traffic sign", attributed_source="Model",
         action="Ghép thêm model từ vựng mở cho traffic sign", status="Đã áp dụng", measurable=True,
         side_group="Box thừa"),
    dict(rec_id="KN-04", scope="F", error_group="Sai class", class_name="truck", attributed_source="Guideline",
         action="Guideline v2: tách rõ truck và bus, kèm ảnh ví dụ", status="Đã áp dụng", measurable=True,
         side_group=None),
    dict(rec_id="KN-05", scope="D", error_group="Lỗi box", class_name="car", attributed_source="Model",
         action="Hậu xử lý co box 5%", status="Bỏ qua", measurable=True, side_group=None),
    dict(rec_id="KN-06", scope="B", error_group="Bỏ sót vật", class_name="traffic light", attributed_source="Annotator",
         action="Ghi chú coaching: chạy 640px với ảnh có đèn", status="Đã duyệt", measurable=False,
         side_group=None),
    dict(rec_id="KN-07", scope="R1", error_group="Lỗi box", class_name="car", attributed_source="Reviewer",
         action="Ghi chú hiệu chỉnh: thống nhất mức lệch box chấp nhận được", status="Đề xuất", measurable=False,
         side_group=None),
]

COMMENTS = {
    "Bỏ sót vật": ["Thiếu box cho {cls} ở vùng này.", "Còn một {cls} chưa được gán.", "Sót {cls}, xem lại góc này."],
    "Box quá lớn": ["Box rộng quá, thừa nhiều nền quanh {cls}.", "Thu box lại cho sát {cls}."],
    "Box quá nhỏ": ["Box chưa ôm hết {cls}.", "Box hụt, mở rộng cho đủ {cls}."],
    "Box lệch": ["Box bị lệch so với {cls}.", "Căn lại box, đang trượt khỏi {cls}."],
    "Box bị cắt": ["{cls} nằm sát mép ảnh, box phải kéo ra tới mép.", "Box dừng sớm, chưa chạm mép ảnh."],
    "Sai class": ["Đây là {cls}, không phải {pred}.", "Nhãn sai, vật này là {cls}."],
    "Trùng lặp": ["Hai box cho cùng một {cls}, xoá bớt một.", "Box này trùng với box bên cạnh."],
    "Box thừa": ["Không có {cls} nào ở đây, xoá box.", "Box này không ôm vật nào."],
    "Mơ hồ": ["Vật quá nhỏ, guideline chưa nói rõ có gán không.", "Người ngồi trên xe: gán rider hay person? Cần thống nhất."],
}

_BOX_COLS = ["sx1", "sy1", "sx2", "sy2"]
_GT_COLS = ["gx1", "gy1", "gx2", "gy2"]
_ISSUE_ITEM_COLS = ["annotator", "image", "object_id", "class_name", "class_pred", "group", "error_type",
                    "size_bucket", "occluded", "truncated", "source", "is_false_alarm", "item_key",
                    *_BOX_COLS, *_GT_COLS]


# ---------- đáp án ----------

def load_ground_truth(xml_path=S.GT_XML) -> pd.DataFrame:
    root = ET.parse(xml_path).getroot()
    rows = []
    for im in root.findall("image"):
        w, h = float(im.get("width")), float(im.get("height"))
        for b in im.findall("box"):
            attrs = {a.get("name"): a.text for a in b.findall("attribute")}
            rows.append((im.get("name"), w, h, b.get("label"),
                         float(b.get("xtl")), float(b.get("ytl")), float(b.get("xbr")), float(b.get("ybr")),
                         b.get("occluded") == "1", attrs.get("truncated") == "true"))
    df = pd.DataFrame(rows, columns=["image", "img_w", "img_h", "class_name", "x1", "y1", "x2", "y2",
                                     "occluded", "truncated"])
    df.insert(0, "object_id", np.arange(len(df)))
    bw, bh = df["x2"] - df["x1"], df["y2"] - df["y1"]
    df["size_bucket"] = np.select([bw * bh < 32 ** 2, bw * bh < 96 ** 2], ["Nhỏ", "Vừa"], "Lớn")
    df["tiny"] = np.minimum(bw, bh) < 10
    return df


def _assign_jobs(objects, rng):
    images = np.array(sorted(objects["image"].unique()))
    images = images[rng.permutation(len(images))]
    half = len(images) // 2
    per_job = int(np.ceil(half / JOBS_PER_BATCH))
    pos = np.arange(len(images))
    within = np.where(pos < half, pos, pos - half)
    return pd.DataFrame({"image": images, "batch": np.where(pos < half, 1, 2),
                         "job_idx": np.minimum(within // per_job + 1, JOBS_PER_BATCH)})


# ---------- annotator ----------

def _latents(n, rng):
    families = sorted({a["family"] for a in ANNOTATORS})
    return {"obj": rng.random((3, n)),
            "fam": {f: rng.random((3, n)) for f in families},
            "ind": {name: rng.random((6, n)) for name in NAMES},
            "pick": rng.integers(0, 1000, n)}


def _mix(lat, a, k):
    """Biến ngẫu nhiên đều, trộn phần chung của vật, của họ model và của riêng annotator.

    Phần chung làm các annotator cùng họ sai trên cùng một vật, giống model thật.
    """
    z = 0.45 * lat["obj"][k] + 0.30 * lat["fam"][a["family"]][k] + 0.25 * lat["ind"][a["annotator"]][k]
    return (np.argsort(np.argsort(z)) + 0.5) / len(z)


def _factor(table, name, cls):
    out = np.ones(len(cls))
    for (who, c), v in (table or {}).items():
        if who == name:
            out = np.where(cls == c, v, out)
    return out


def _simulate_objects(objects, lat, tweaks):
    cls = objects["class_name"].to_numpy()
    size = objects["size_bucket"].to_numpy()
    occl = objects["occluded"].to_numpy()
    trunc = objects["truncated"].to_numpy()
    tiny = objects["tiny"].to_numpy()
    gt = objects[["x1", "y1", "x2", "y2"]].to_numpy()
    w, h = gt[:, 2] - gt[:, 0], gt[:, 3] - gt[:, 1]
    cls_mult = objects["class_name"].map(CLS_MULT).to_numpy()
    target = np.array([CONFUSE[c][k % len(CONFUSE[c])] for c, k in zip(cls, lat["pick"])], dtype=object)

    frames = []
    for a in ANNOTATORS:
        name, coco = a["annotator"], a["family"] != OPEN_VOCAB
        ind = lat["ind"][name]

        p = a["miss"] * np.select([size == "Nhỏ", size == "Vừa"], [1.6, 0.75], 0.35)
        p = p * np.where(occl, 1.2, 1.0) * np.where(tiny, 1.3, 1.0)
        if name == "B":
            p = p * np.where(size == "Nhỏ", 1.25, 1.0)
        if coco:  # COCO không có class traffic sign, chỉ có stop sign
            p = np.where(cls == "traffic sign", 0.96, p)
        p = p * _factor(tweaks.get("miss_mult"), name, cls)
        for (who, c), v in tweaks.get("miss_set", {}).items():
            if who == name:
                p = np.where(cls == c, v, p)
        missed = _mix(lat, a, 0) < np.clip(p, 0, 0.98)

        pc = a["cls"] * cls_mult
        pc = np.where(cls == "rider", 0.95 if coco else 0.40, pc)  # COCO gộp rider vào person
        pc = pc * _factor(tweaks.get("cls_mult"), name, cls)
        wrong = ~missed & (_mix(lat, a, 1) < np.clip(pc, 0, 0.98))

        pb = a["box"] * np.where(trunc, 2.2, 1.0) * np.where(occl, 1.3, 1.0) * np.where(size == "Nhỏ", 1.2, 1.0)
        boxerr = ~missed & ~wrong & (_mix(lat, a, 2) < np.clip(pb, 0, 0.9))

        fix_u = ind[3]
        fixed_miss = missed & (fix_u < max(a["fix_miss"], a["fix_all"]))
        fixed_cls = wrong & (fix_u < max(a["fix_cls"], a["fix_all"]))
        fixed_box = boxerr & (fix_u < a["fix_all"])
        missed, wrong, boxerr = missed & ~fixed_miss, wrong & ~fixed_cls, boxerr & ~fixed_box

        small_w, large_w = a["box_mix"]
        subtype = np.select([trunc & (ind[4] < 0.6), ind[5] < small_w, ind[5] < small_w + large_w],
                            ["Box bị cắt", "Box quá nhỏ", "Box quá lớn"], "Box lệch")
        group = np.select([missed, wrong, boxerr], ["Bỏ sót vật", "Sai class", "Lỗi box"], "Đúng")
        error_type = np.where(boxerr, subtype, np.where(group == "Đúng", "", group))
        source = np.select([missed, fixed_miss, fixed_cls | fixed_box], ["Không có box", "manual", "semi-auto"], "auto")

        box = gt + (ind[5][:, None] - 0.5) * 3
        grow = np.select([error_type == "Box quá lớn", error_type == "Box quá nhỏ"], [0.18, -0.15], 0.0)
        box[:, 0] -= grow * w
        box[:, 1] -= grow * h
        box[:, 2] += grow * w
        box[:, 3] += grow * h
        shift = error_type == "Box lệch"
        box[shift] += np.stack([0.28 * w, 0.2 * h, 0.28 * w, 0.2 * h], axis=1)[shift]
        cut = error_type == "Box bị cắt"
        box[cut, 2] -= 0.3 * w[cut]
        box[missed] = np.nan

        pred = np.where(wrong, target, cls).astype(object)
        pred[missed] = None
        frame = pd.DataFrame({
            "annotator": name, "object_id": objects["object_id"].to_numpy(), "image": objects["image"].to_numpy(),
            "class_true": cls, "class_pred": pred, "drawn": ~missed, "group": group, "error_type": error_type,
            "source": source, "size_bucket": size, "occluded": occl, "truncated": trunc, "tiny": tiny,
        })
        frame[_BOX_COLS] = box
        frame[_GT_COLS] = gt
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _extras_pool(objects, rng):
    """Hồ box thừa và box trùng, sinh dư gấp đôi để lần pilot có thể giảm hoặc tăng."""
    rows = []
    by_image = {img: g for img, g in objects.groupby("image")}
    for a in ANNOTATORS:
        for img, objs in by_image.items():
            img_w, img_h = objs["img_w"].iat[0], objs["img_h"].iat[0]
            for _ in range(rng.poisson(a["extra"] * 2)):
                if rng.random() < 0.25:
                    o = objs.iloc[rng.integers(len(objs))]
                    jx = rng.normal(0, 0.06 * (o["x2"] - o["x1"]))
                    jy = rng.normal(0, 0.06 * (o["y2"] - o["y1"]))
                    box = (o["x1"] + jx, o["y1"] + jy, o["x2"] + jx, o["y2"] + jy)
                    cls, size, group = o["class_name"], o["size_bucket"], "Trùng lặp"
                else:
                    cls = str(rng.choice(FP_CLASSES, p=FP_PROBS))
                    size = str(rng.choice(S.SIZES, p=[0.6, 0.3, 0.1]))
                    side = {"Nhỏ": 22, "Vừa": 60, "Lớn": 130}[size] * rng.uniform(0.7, 1.3)
                    cx, cy = rng.uniform(side, img_w - side), rng.uniform(img_h * 0.25, img_h - side)
                    box = (cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2)
                    group = "Box thừa"
                rows.append((a["annotator"], img, cls, group, size, *box, rng.random(), rng.random(), *rng.random(3)))
    pool = pd.DataFrame(rows, columns=["annotator", "image", "class_pred", "group", "size_bucket",
                                       *_BOX_COLS, "keep_u", "fix_u", "r0", "r1", "r2"])
    pool.insert(0, "extra_id", np.arange(len(pool)))
    return pool


def _select_extras(pool, tweaks):
    coco = pool["annotator"].map(lambda n: BY_NAME[n]["family"] != OPEN_VOCAB).to_numpy()
    base = np.where(coco & (pool["class_pred"] == "traffic sign"), 0.15, 1.0)
    mult = np.ones(len(pool))
    for (who, c), v in tweaks.get("extra_mult", {}).items():
        mult = np.where((pool["annotator"] == who) & (pool["class_pred"] == c), v, mult)
    keep = pool["keep_u"].to_numpy() < 0.5 * base * mult
    keep &= pool["fix_u"].to_numpy() >= pool["annotator"].map(lambda n: BY_NAME[n]["fix_all"]).to_numpy()
    return pool[keep]


# ---------- reviewer ----------

def _review(run, batch, sub_obj, sub_ext, img_jobs, rev_u):
    out = {"issues": [], "assign": [], "work": [], "overlap": []}
    prefix = "P" if run == S.RUN_PILOT else "L"
    for ai, name in enumerate(NAMES):
        so = sub_obj[sub_obj["annotator"] == name]
        se = sub_ext[sub_ext["annotator"] == name]
        for j in range(1, JOBS_PER_BATCH + 1):
            imgs = img_jobs.loc[(img_jobs["batch"] == batch) & (img_jobs["job_idx"] == j), "image"].to_numpy()
            frame_rng = np.random.default_rng([SEED, batch, j, ai])
            reviewed = frame_rng.choice(imgs, size=min(FRAMES_REVIEWED, len(imgs)), replace=False)
            o = so[so["image"].isin(reviewed)]
            e = se[se["image"].isin(reviewed)]
            job_order = (batch - 1) * JOBS_PER_BATCH + j
            job_id = f"{prefix}{batch}-{name}-J{j}"
            # Phân công lệch: mỗi annotator chủ yếu gặp hai trong ba reviewer, như thực tế hay xảy ra.
            first = (ai + job_order % 2) % len(REVIEWERS)
            reviewer_ids = [first]
            if (ai * JOBS_PER_BATCH + job_order) % 5 == 0:  # khoảng 20% job được chấm hai lần
                reviewer_ids.append((first + 1) % len(REVIEWERS))

            flagged = []
            for k, ri in enumerate(reviewer_ids):
                r = REVIEWERS[ri]
                u = rev_u[ri, ai][o["object_id"].to_numpy()]
                is_err = (o["group"] != "Đúng").to_numpy()
                caught = is_err & (u[:, 0] < o["group"].map(r["catch"]).fillna(0).to_numpy())
                alarm = ~is_err & (u[:, 0] < r["fa"])
                picked = caught | alarm

                io = o[picked].copy()
                up = u[picked]
                io["is_false_alarm"] = alarm[picked]
                fa_type = np.select([up[:, 1] < 0.7, up[:, 1] < 0.85], ["Box lệch", "Box quá lớn"], "Box quá nhỏ")
                io["error_type"] = np.where(io["is_false_alarm"], fa_type, io["error_type"])
                io["group"] = np.where(io["is_false_alarm"], "Lỗi box", io["group"])
                vague = ~io["is_false_alarm"] & (up[:, 2] < 0.45) & (
                    ((io["group"] == "Bỏ sót vật") & io["tiny"])
                    | ((io["group"] == "Sai class") & io["class_true"].isin(["rider", "person"])))
                io.loc[vague, ["group", "error_type"]] = "Mơ hồ"
                io["class_name"] = io["class_true"]
                io["item_key"] = "O" + io["object_id"].astype(str)

                ie = e[e[f"r{ri}"] < e["group"].map(r["catch"])].copy()
                ie["class_name"] = ie["class_pred"]
                ie["error_type"] = ie["group"]
                ie["item_key"] = "E" + ie["extra_id"].astype(str)
                ie = ie.assign(object_id=-1, occluded=False, truncated=False, source="auto", is_false_alarm=False,
                               gx1=np.nan, gy1=np.nan, gx2=np.nan, gy2=np.nan)

                found = pd.concat([io[_ISSUE_ITEM_COLS], ie[_ISSUE_ITEM_COLS]], ignore_index=True)
                found = found.assign(run=run, batch=batch, job_id=job_id, job_order=job_order,
                                     reviewer=r["reviewer"], is_second_review=k == 1)
                out["issues"].append(found)

                drawn = o[o["drawn"]]
                reviewed_items = pd.concat([
                    drawn[["class_true", "size_bucket"]].rename(columns={"class_true": "class_name"}),
                    e[["class_pred", "size_bucket"]].rename(columns={"class_pred": "class_name"}),
                    io.loc[io["source"] == "Không có box", ["class_name", "size_bucket"]],
                ])
                work = reviewed_items.groupby(["class_name", "size_bucket"]).size().rename("n_reviewed").reset_index()
                out["work"].append(work.assign(run=run, job_id=job_id, job_order=job_order, annotator=name,
                                               reviewer=r["reviewer"]))
                out["assign"].append(dict(
                    run=run, batch=batch, job_id=job_id, job_order=job_order, annotator=name,
                    reviewer=r["reviewer"], is_second_review=k == 1, n_frames=len(reviewed),
                    n_annotations=len(drawn) + len(e), n_true_errors=int(is_err.sum()) + len(e),
                    n_issues=len(found), n_false_alarms=int(alarm.sum())))
                flagged.append((r["reviewer"], set(found["item_key"])))

            if len(flagged) == 2:
                (ra, sa), (rb, sb) = sorted(flagged, key=lambda t: t[0])
                out["overlap"].append(dict(run=run, job_id=job_id, annotator=name, reviewer_a=ra, reviewer_b=rb,
                                           n_both=len(sa & sb), n_only_a=len(sa - sb), n_only_b=len(sb - sa)))
    return out


# ---------- issue: thời gian, phản hồi, lặp lại, quy nguồn ----------

def _enrich_issues(issues, rng):
    m = len(issues)
    u = rng.random((6, m))
    issues.insert(0, "issue_id", [f"ISS-{i:05d}" for i in range(1, m + 1)])
    issues = issues.rename(columns={"group": "error_group"})
    issues["model"] = issues["annotator"].map(lambda n: BY_NAME[n]["model"])

    day = (issues["job_order"] - 1) * 2 + np.where(issues["run"] == S.RUN_PILOT, 7, 0)
    issues["created_at"] = BASE_TIME + pd.to_timedelta(day, unit="D") + pd.to_timedelta(u[0] * 8, unit="h")
    issues["fix_arm"] = np.where(u[1] < 0.4, S.ARM_AGENT, S.ARM_ANNOTATOR)

    vague = (issues["error_group"] == "Mơ hồ").to_numpy()
    no_box = (issues["source"] == "Không có box").to_numpy()
    issues["requested_action"] = np.where(vague, np.where(no_box, "Thêm box", "Đổi class"),
                                          issues["error_group"].map(ACTION_OF))

    alarm = issues["is_false_alarm"].to_numpy()
    p_right = np.where(alarm, 0.15, issues["annotator"].map(lambda n: RESPONSE[n][0]))
    p_other = np.where(alarm, 0.0, issues["annotator"].map(lambda n: RESPONSE[n][1]))
    still_open = u[2] < np.where(vague, 0.35, 0.10)
    outcome = np.select([still_open, u[3] < p_right, u[3] < p_right + p_other],
                        ["Chưa xử lý", "Sửa đúng yêu cầu", "Sửa khác yêu cầu"], "Đóng mà không sửa")
    requested = issues["requested_action"].to_numpy()
    other = np.array([OTHER_ACTION[act][i % 2] for i, act in enumerate(requested)])
    # Vùng reviewer đánh dấu: quanh box đã nộp, hoặc quanh chỗ lẽ ra phải có box.
    sub, gt = issues[_BOX_COLS].to_numpy(), issues[_GT_COLS].to_numpy()
    issues[["ix1", "iy1", "ix2", "iy2"]] = np.where(np.isnan(sub), gt, sub) + np.array([-4, -4, 4, 4])
    issues["fix_outcome"] = outcome
    issues["observed_change"] = np.select(
        [outcome == "Sửa đúng yêu cầu", outcome == "Sửa khác yêu cầu", outcome == "Đóng mà không sửa"],
        [requested, other, "Không đổi"], "Chưa xử lý")
    issues["still_wrong"] = np.select(
        [outcome == "Sửa đúng yêu cầu", outcome == "Sửa khác yêu cầu", outcome == "Đóng mà không sửa"],
        [u[4] < np.where(alarm, 0.30, 0.08), u[4] < 0.60, ~alarm], True)
    issues["resolved"] = outcome != "Chưa xử lý"

    issues["attributed_source"] = np.select([
        alarm,
        vague,
        (issues["error_group"] == "Sai class") & issues["class_name"].isin(["truck", "bus", "rider", "bike", "motor"]),
        (issues["class_name"] == "traffic sign") & (issues["error_group"] == "Bỏ sót vật") & (issues["annotator"] != "F"),
        (issues["annotator"] == "A") & issues["error_group"].isin(["Box thừa", "Trùng lặp"]),
        (issues["annotator"] == "B") & (issues["error_group"] == "Bỏ sót vật") & (issues["size_bucket"] == "Nhỏ"),
        (issues["annotator"] == "F") & (issues["error_group"] == "Sai class"),
    ], ["Reviewer", "Guideline", "Guideline", "Model", "Model", "Annotator", "Guideline"], "Chưa đủ bằng chứng")

    variant = rng.integers(0, 6, m)
    issues["comment"] = [
        COMMENTS[t][v % len(COMMENTS[t])].format(cls=c, pred=p or "?")
        for t, v, c, p in zip(issues["error_type"], variant, issues["class_name"], issues["class_pred"])]
    issues["reply"] = np.select(
        [alarm & (u[5] < 0.6), ~alarm & (u[5] < 0.12)],
        ["Mình thấy box đã sát vật rồi, bạn xem lại giúp.", "Đã sửa, nhờ bạn kiểm tra lại."], None)
    return issues


def _build_patches(issues, rng):
    ag = issues[issues["fix_arm"] == S.ARM_AGENT].reset_index(drop=True)
    k = len(ag)
    u = rng.random((9, k))
    op = ag["requested_action"]
    alarm = ag["is_false_alarm"].to_numpy()

    mapped = u[0] < 0.93
    proposed = mapped & (u[1] < op.map({"Đổi class": 0.97, "Xoá box": 0.97, "Thêm box": 0.90, "Chỉnh box": 0.65}).to_numpy())
    p_ok = np.where(alarm, 0.05, op.map({"Đổi class": 0.88, "Xoá box": 0.93, "Thêm box": 0.70, "Chỉnh box": 0.62}))
    correct = proposed & (u[2] < p_ok)
    decided = proposed & (u[3] < 0.90)
    p_accept = np.where(correct, 0.85, 0.22)  # 0.22: người duyệt tin nhầm đề xuất sai
    p_edit = np.where(correct, 0.08, 0.28)
    decision = np.select(
        [~mapped, ~proposed, ~decided, u[4] < p_accept, u[4] < p_accept + p_edit],
        ["Không map được", "Không đề xuất được", "Chờ duyệt", "Chấp nhận", "Sửa rồi chấp nhận"], "Từ chối")
    accepted, edited, rejected = decision == "Chấp nhận", decision == "Sửa rồi chấp nhận", decision == "Từ chối"
    applied = (accepted | edited) & (u[5] < 0.97)
    final_correct = (applied & np.where(accepted, correct, u[6] < 0.9)) | (rejected & alarm)
    closed = applied & (u[7] < 0.88)

    sub = ag[_BOX_COLS].to_numpy()
    gt = ag[_GT_COLS].to_numpy()
    anchor = np.where(np.isnan(gt), sub, gt)
    width = (anchor[:, 2] - anchor[:, 0])[:, None]
    good = anchor + (u[8][:, None] - 0.5) * 3
    bad = anchor + np.concatenate([0.35 * width, 0 * width, 0.35 * width, 0 * width], axis=1)
    redraw = op.isin(["Thêm box", "Chỉnh box"]).to_numpy()[:, None]
    prop_box = np.where(redraw, np.where(correct[:, None], good, bad), sub)
    prop_box[(op == "Xoá box").to_numpy() | ~proposed] = np.nan
    wrong_cls = ag["class_name"].map(lambda c: CONFUSE[c][0])
    prop_cls = np.where(op.isin(["Đổi class", "Thêm box"]), np.where(correct, ag["class_name"], wrong_cls), ag["class_pred"])
    prop_cls = np.where((op == "Xoá box") | ~proposed, None, prop_cls)

    final_box = np.where(accepted[:, None], prop_box, np.where(edited[:, None], gt, sub))
    final_cls = np.where(accepted, prop_cls, np.where(edited, ag["class_name"], ag["class_pred"]))
    final_cls = np.where(np.isnan(final_box[:, 0]), None, final_cls)

    patches = pd.DataFrame({
        "patch_id": [f"PV-{i:05d}" for i in range(1, k + 1)], "issue_id": ag["issue_id"], "run": ag["run"],
        "annotator": ag["annotator"], "class_name": ag["class_name"], "error_group": ag["error_group"],
        "operation": op, "is_false_alarm": alarm, "mapped": mapped, "proposed": proposed,
        "proposal_correct": correct, "decision": decision, "applied": applied, "final_correct": final_correct,
        "issue_closed": closed,
        "iou_proposed_final": np.select([accepted, edited], [1.0, 0.5 + 0.42 * u[6]], np.nan),
        "minutes_to_decide": np.where(decided, np.exp(np.log(np.select([accepted, edited], [0.6, 2.0], 1.0))
                                                     + 0.5 * rng.standard_normal(k)), np.nan),
        "proposed_class": prop_cls, "final_class": final_cls,
    })
    patches[["px1", "py1", "px2", "py2"]] = prop_box
    patches[["fx1", "fy1", "fx2", "fy2"]] = final_box
    return patches


def _finish_issues(issues, patches, rng):
    """Chốt trạng thái đóng, thời gian xử lý và cờ lặp lại."""
    agent = (issues["fix_arm"] == S.ARM_AGENT).to_numpy()
    by_issue = patches.set_index("issue_id")
    closed = issues["issue_id"].map(by_issue["issue_closed"]).eq(True).to_numpy()
    final_ok = issues["issue_id"].map(by_issue["final_correct"]).eq(True).to_numpy()
    stopped = issues["issue_id"].map(by_issue["decision"]).isin(
        ["Từ chối", "Không map được", "Không đề xuất được"]).to_numpy()
    u = rng.random((2, len(issues)))
    # Bản vá không đi tiếp được thì issue quay về sửa tay, chậm hơn một chút.
    fallback = agent & ~closed & stopped & (u[0] < 0.75)
    issues["resolved"] = np.where(agent, closed | fallback, issues["resolved"])
    issues["still_wrong"] = np.where(agent, np.where(fallback, u[1] < 0.15, ~final_ok), issues["still_wrong"])
    issues.loc[agent, ["fix_outcome", "observed_change"]] = None

    speed = np.where(agent & closed, 0.35, np.where(fallback, 1.2, 1.0))
    median = issues["error_group"].map(RESOLVE_MEDIAN_H) * speed
    hours = np.exp(np.log(median) + 0.7 * rng.standard_normal(len(issues)))
    issues["resolution_hours"] = np.where(issues["resolved"], hours, np.nan)
    issues["resolved_at"] = issues["created_at"] + pd.to_timedelta(issues["resolution_hours"], unit="h")

    # Lặp lại: cùng annotator đã có cùng loại lỗi ở một job trước đó. Pilot nối tiếp lô 1.
    issues["is_recurrent"] = False
    for later in (S.RUN_CTRL, S.RUN_PILOT):
        line = issues[issues["run"].isin([S.RUN_B1, later])]
        first = line.groupby(["annotator", "error_type"])["job_order"].transform("min")
        rows = line.index if later == S.RUN_CTRL else line.index[line["run"] == later]
        issues.loc[rows, "is_recurrent"] = (line["job_order"] > first)[rows]
    return issues


# ---------- chấm chéo giữa annotator ----------

def _cross_tables(objects, sub_obj, sub_ext):
    cls = objects["class_name"].to_numpy()
    size = objects["size_bucket"].to_numpy()
    img_code, img_names = pd.factorize(objects["image"])
    n_img = len(img_names)

    drawn, pred, box_ok, err = {}, {}, {}, {}
    for name in NAMES:
        s = sub_obj[sub_obj["annotator"] == name].sort_values("object_id")
        drawn[name] = s["drawn"].to_numpy()
        pred[name] = s["class_pred"].to_numpy()
        box_ok[name] = (s["group"] != "Lỗi box").to_numpy()
        err[name] = (s["group"] != "Đúng").to_numpy()
    ext_by_key = sub_ext.groupby(["annotator", "class_pred", "size_bucket"]).size()
    ext_by_img = {name: np.bincount(pd.Categorical(g["image"], categories=img_names).codes, minlength=n_img)
                  for name, g in sub_ext.groupby("annotator")}
    for name in NAMES:
        ext_by_img.setdefault(name, np.zeros(n_img, dtype=int))

    def extras_of(name, col):
        if name not in ext_by_key.index.get_level_values(0):
            return pd.DataFrame(columns=["class_name", "size_bucket", col])
        return ext_by_key[name].rename(col).reset_index().rename(columns={"class_pred": "class_name"})

    pair_rows = []
    img_same, img_total = np.zeros(n_img), np.zeros(n_img)
    for a in NAMES:
        for b in NAMES:
            if a == b:
                continue
            both = drawn[a] & drawn[b]
            same_cls = both & (pred[a] == pred[b])
            cols = {
                "n_same": same_cls & box_ok[a] & box_ok[b],
                "n_box_off": same_cls & ~(box_ok[a] & box_ok[b]),
                "n_class_diff": both & ~same_cls,
                "n_only_a": drawn[a] & ~drawn[b],
                "n_only_b": ~drawn[a] & drawn[b],
            }
            g = pd.DataFrame({"class_name": cls, "size_bucket": size, **cols})
            g = pd.concat([g, extras_of(a, "n_only_a"), extras_of(b, "n_only_b")]).fillna(0)
            g = g.groupby(["class_name", "size_bucket"], as_index=False).sum()
            pair_rows.append(g.assign(annotator_a=a, annotator_b=b))
            if a < b:
                img_same += np.bincount(img_code, weights=cols["n_same"], minlength=n_img)
                img_total += np.bincount(img_code, weights=drawn[a] | drawn[b], minlength=n_img)
                img_total += ext_by_img[a] + ext_by_img[b]
    count_cols = ["n_same", "n_class_diff", "n_box_off", "n_only_a", "n_only_b"]
    pairs = pd.concat(pair_rows, ignore_index=True)
    pairs[count_cols] = pairs[count_cols].astype(int)
    pairs = pairs[["annotator_a", "annotator_b", "class_name", "size_bucket", *count_cols]]

    n_obj_img = np.bincount(img_code, minlength=n_img)
    err_rate = np.mean([(np.bincount(img_code, weights=err[name], minlength=n_img) + ext_by_img[name])
                        / (n_obj_img + ext_by_img[name]) for name in NAMES], axis=0)
    image_scores = pd.DataFrame({"image": img_names, "n_objects": n_obj_img,
                                 "agreement": img_same / np.maximum(img_total, 1), "error_rate": err_rate})

    votes = pd.DataFrame({
        "object_key": "O" + objects["object_id"].astype(str), "image": objects["image"],
        "class_name": cls, "size_bucket": size,
        "n_votes": np.sum([drawn[name] for name in NAMES], axis=0), "in_gt": True})
    extra_votes = pd.DataFrame({
        "object_key": "E" + sub_ext["extra_id"].astype(str), "image": sub_ext["image"],
        "class_name": sub_ext["class_pred"], "size_bucket": sub_ext["size_bucket"], "n_votes": 1, "in_gt": False})
    votes = pd.concat([votes, extra_votes], ignore_index=True)

    score_rows = []
    for name in NAMES:
        g = pd.DataFrame({"class_name": cls, "size_bucket": size, "n_objects": 1,
                          "n_drawn": drawn[name], "n_correct": ~err[name]})
        g = pd.concat([g, extras_of(name, "n_drawn")]).fillna(0)
        score_rows.append(g.groupby(["class_name", "size_bucket"], as_index=False).sum().assign(annotator=name))
    scores = pd.concat(score_rows, ignore_index=True)
    scores[["n_objects", "n_drawn", "n_correct"]] = scores[["n_objects", "n_drawn", "n_correct"]].astype(int)
    scores = scores[["annotator", "class_name", "size_bucket", "n_objects", "n_drawn", "n_correct"]]
    return pairs, votes, scores, image_scores


def _build_recommendations(issues, workload):
    def rate(run, scope, group, cls):
        who = "reviewer" if scope.startswith("R") else "annotator"
        i = issues[(issues["run"] == run) & (issues[who] == scope) & (issues["class_name"] == cls)]
        w = workload[(workload["run"] == run) & (workload[who] == scope) & (workload["class_name"] == cls)]
        hits, total = int((i["error_group"] == group).sum()), w["n_reviewed"].sum()
        return (hits / total * 100 if total else np.nan), hits

    rows = []
    for rec in RECOMMENDATIONS:
        args = (rec["scope"], rec["error_group"], rec["class_name"])
        rate_control, n_control = rate(S.RUN_CTRL, *args)
        row = dict(rec, n_control=n_control, rate_control=rate_control, rate_pilot=np.nan,
                   side_rate_control=np.nan, side_rate_pilot=np.nan)
        if rec["measurable"]:
            row["rate_pilot"] = rate(S.RUN_PILOT, *args)[0]
            if rec["side_group"]:
                side = (rec["scope"], rec["side_group"], rec["class_name"])
                row["side_rate_control"] = rate(S.RUN_CTRL, *side)[0]
                row["side_rate_pilot"] = rate(S.RUN_PILOT, *side)[0]
        rows.append(row)
    return pd.DataFrame(rows)


# ---------- điểm vào ----------

def build_all() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    objects = load_ground_truth()
    img_jobs = _assign_jobs(objects, rng)
    lat = _latents(len(objects), rng)
    pool = _extras_pool(objects, rng)
    rev_u = rng.random((len(REVIEWERS), len(ANNOTATORS), len(objects), 3))

    obj_ctrl, ext_ctrl = _simulate_objects(objects, lat, {}), _select_extras(pool, {})
    obj_pilot, ext_pilot = _simulate_objects(objects, lat, PILOT_TWEAKS), _select_extras(pool, PILOT_TWEAKS)
    reviews = [
        _review(S.RUN_B1, 1, obj_ctrl, ext_ctrl, img_jobs, rev_u),
        _review(S.RUN_CTRL, 2, obj_ctrl, ext_ctrl, img_jobs, rev_u),
        _review(S.RUN_PILOT, 2, obj_pilot, ext_pilot, img_jobs, rev_u),
    ]

    def gather(key):
        return [item for r in reviews for item in r[key]]

    issues = _enrich_issues(pd.concat(gather("issues"), ignore_index=True), rng)
    patches = _build_patches(issues, rng)
    issues = _finish_issues(issues, patches, rng).drop(columns="item_key")
    workload = pd.concat(gather("work"), ignore_index=True)
    workload = workload[["run", "job_id", "job_order", "annotator", "reviewer", "class_name", "size_bucket", "n_reviewed"]]
    pairs, votes, scores, image_scores = _cross_tables(objects, obj_ctrl, ext_ctrl)

    # Bên trong file này làm việc với nhãn cho dễ đọc. Đầu ra đổi về đúng dạng hợp đồng (dùng mã),
    # để bảng giả đi qua cùng một cửa kiểm tra với bảng thật.
    tables = {
        "issues": issues,
        "workload": workload,
        "review_assignments": pd.DataFrame(gather("assign")),
        "reviewer_overlap": pd.DataFrame(gather("overlap")),
        "pair_agreement": pairs,
        "object_votes": votes,
        "gt_scores": scores,
        "image_scores": image_scores,
        "patches": patches,
        "recommendations": _build_recommendations(issues, workload),
        "annotators": pd.DataFrame(ANNOTATORS)[["annotator", "model", "family", "config"]],
        "reviewers": pd.DataFrame(REVIEWERS)[["reviewer", "style"]],
    }
    return {name: codec.encode(name, df) for name, df in tables.items()}
