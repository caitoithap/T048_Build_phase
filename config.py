import os
import sys
import site
import ctypes
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")
load_dotenv(Path.home() / ".env")

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

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sample_data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# QC Rule-based Thresholds
MIN_BBOX_SIZE_PX = 15.0       # Minimum allowed width or height for valid Bbox
MAX_ASPECT_RATIO = 6.5        # Max ratio between W/H or H/W
DUPLICATE_IOU_THRESH = 0.85   # IoU threshold above which boxes are flagged as duplicates

# Defaults for Detector & Pre-labeling pipeline
DEFAULT_MODEL = "yolov8n.pt"
DEFAULT_CONF_THRESHOLD = 0.35
DEFAULT_MIN_BOX_SIZE = MIN_BBOX_SIZE_PX
DEFAULT_MAX_BOX_ASPECT_RATIO = MAX_ASPECT_RATIO
TARGET_CLASSES = ["car", "bus", "truck", "person", "bicycle", "motorcycle", "traffic light"]

# Model-assisted Audit Thresholds
AUDIT_MODEL_NAME = "yolov8n.pt"  # Ultra-lightweight CPU ONNX model
MODEL_ASSIST_CONF = 0.70        # High confidence required for AI to flag missing human box

# Google Gemini API Settings for AI QC Auditor Agent
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
