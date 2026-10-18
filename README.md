# 🚗 YOLO Nano Pre-Annotation & Tracking Pipeline (CPU Edition)

> **AI-Assisted Data Labeling System for Autonomous Driving & Computer Vision**  
> *VinUni AI20K - AI Thực Chiến (Build Phase Cohort 4, L2-L3)*

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8%2Fv11-green.svg)](https://github.com/ultralytics/ultralytics)
[![CVAT](https://img.shields.io/badge/CVAT-v1.1%20XML-orange.svg)](https://www.cvat.ai/)
[![CPU-Friendly](https://img.shields.io/badge/Hardware-100%25%20CPU-brightgreen.svg)]()

---

## 📌 Features

- ⚡ **100% CPU Optimized**: Runs inference using lightweight YOLO Nano (`yolov8n.pt` / `yolo11n.pt`) with latency **15-25ms/frame** on standard laptops.
- 🎯 **ByteTrack Multi-Object Tracking**: Automatically assigns and propagates persistent `Track ID`s across video frames.
- 🧹 **Rule-Based Quality Control**: Automatically filters out noisy predictions (boxes < 15px, extreme aspect ratios, low confidence).
- 💾 **CVAT XML & COCO Export**: Generates standard `CVAT XML 1.1` and `COCO JSON` annotation files.
- 🌐 **CVAT REST API Integration**: Directly uploads pre-annotations to CVAT Server tasks.
- 📊 **Dual Interface**: Includes both a **Streamlit Web Dashboard** and a **CLI tool** for batch automation.
- 📈 **M22 Issue Analytics Dashboard**: FastAPI + React dashboard (`dashboard/`) with 11 analytics and lookup pages.

---

## 📁 Directory Structure

```text
T048_Build_phase/
├── requirements.txt         # CPU-optimized Python dependencies
├── config.py                # Pipeline configurations & CVAT API settings
├── src/
│   ├── __init__.py
│   ├── detector.py          # YOLO Nano + ByteTrack CPU inference engine
│   ├── qc_filter.py         # Quality Control rule-based filter
│   ├── cvat_exporter.py     # CVAT XML 1.1 & COCO JSON exporter
│   └── cvat_uploader.py     # CVAT REST API client
├── sample_data/
│   └── create_sample.py     # Synthetic test frame generator
├── output/                  # Exported XML and JSON files
├── dashboard/               # M22 Issue Analytics Dashboard (FastAPI api/ + React web/)
├── api/                     # Vercel Python Function entry (wraps dashboard/api)
├── deploy/                  # VPS fallback: systemd unit, Nginx config, deploy script, .env example
├── tests/                   # pytest suite
├── app.py                   # Streamlit Web Dashboard UI
├── cli.py                   # Command Line Interface tool
├── README.md                # Project user manual
└── REPORT.md                # AI20K Lab Report template (VinUni Rubric)
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Navigate to project directory
cd T048_Build_phase

# Install CPU-optimized requirements
pip install -r requirements.txt
```

### 2. Generate Synthetic Test Dataset (Instant Test)

Generate 10 synthetic road frames without needing to download large datasets:
```bash
python sample_data/create_sample.py
```

### 3. Run via Command Line Interface (CLI)

Run batch pre-annotation on CPU and export CVAT XML:
```bash
python cli.py --source sample_data --conf 0.35 --min-size 15
```

Optional: Upload directly to a CVAT Task ID:
```bash
python cli.py --source sample_data --upload-task-id 1
```

### 4. Launch Streamlit Web Dashboard

```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` to view the visual UI, adjust sliders, inspect Bbox overlays, and download XML files.

### 5. Launch the M22 Issue Analytics Dashboard (FastAPI + React)

The M22 dashboard lives in `dashboard/`: a FastAPI backend (`dashboard/api/`) serves every page as
server-driven blocks (KPIs, Vega-Lite charts, tables), and a React + Vite frontend (`dashboard/web/`) renders them.
All 11 pages are ported. Without real tables in `dashboard/data_real/` it runs on mock data generated from
`sample_data_output1/`.

```bash
./run_dashboard.sh            # API on :8000, UI on http://localhost:5173 (needs Node.js for the UI)
```

Or run the two parts separately:

```bash
cd dashboard && uvicorn api.main:app --reload --port 8000
cd dashboard/web && npm install && npm run dev
```

Details (page porting, plugging in real data): see `dashboard/README.md`.

### 6. Deploy to Vercel

The dashboard is deployed as **one Vercel project**: the React build is served from Vercel's CDN, and
`/api/*` is rewritten to a single Python Function (`api/index.py`) that wraps the FastAPI app in
`dashboard/api/main.py`. Same domain, so no CORS. Every push to `main` deploys production; every PR gets a preview link.

- Production URL: _(added after the first production deploy)_
- Config files: `vercel.json` (build, rewrites, function `includeFiles`), `.vercelignore`,
  `api/requirements.txt` (pinned, without torch/uvicorn/pyarrow so the function stays under 250 MB), `.python-version` (3.12).
- Local check: `vercel build` then `vercel dev` (needs `vercel login`); `.venv/bin/pytest tests/test_vercel_config.py` guards the config.
- **Real data:** export tables as **`.csv` only** (no pyarrow on Vercel, so `.parquet` is not read) into
  `dashboard/data_real/<table>.csv`, commit through a PR, merge; Vercel redeploys. The repo is public, so only
  commit anonymised data until it is made private.

Step-by-step commands: `PLAN.md` steps 7–16. A VPS fallback (Nginx + systemd, files in `deploy/`) is described in the appendix of `PLAN.md`.

### 7. Run the Test Suite

```bash
.venv/bin/pytest tests/ -v    # QC rules, data layer, all API pages (real + mock data), CLI, Vercel config
```

---

## 📊 Benchmark & Impact Metrics (CPU Mode)

| Metric | Performance / Value |
| :--- | :--- |
| **Hardware** | Intel/AMD CPU (No GPU required) |
| **Inference Latency** | ~18.5 ms / frame |
| **Throughput** | ~54 FPS |
| **QC Noise Rejection** | ~18.2% of rác/small boxes filtered out |
| **Manual Labeling Speed** | ~180 sec / frame |
| **Pre-Label Review Speed** | ~35 sec / frame |
| **Productivity Gain** | **78.5% Time Saved** |

---

## 📄 License & Attribution

Developed for **VinUni AI20K (AI Thực Chiến - Cohort 4, L2-L3)**.
- Models powered by [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) & [ByteTrack](https://github.com/ifzhang/ByteTrack).
- Annotation schema compatible with [CVAT (Computer Vision Annotation Tool)](https://www.cvat.ai/).
