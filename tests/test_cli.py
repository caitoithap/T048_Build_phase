"""Test suite cho CLI Audit Tool (cli.py)."""
import subprocess
import sys
from pathlib import Path

def test_cli_execution():
    cmd = [
        sys.executable,
        "cli.py",
        "--annotation", "sample_data_output1/annotations.xml",
        "--mock-cvat",
        "--output-report", "output/test_qc_report.html"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "QC AUDIT & ANALYTICS SUMMARY" in res.stdout
    assert Path("output/test_qc_report.html").exists()


def test_cli_no_mock_cvat():
    cmd = [
        sys.executable,
        "cli.py",
        "--annotation", "sample_data_output1/annotations.xml",
        "--no-mock-cvat",
        "--output-report", "output/test_qc_report_nomock.html"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert "Ingesting Live CVAT" not in res.stdout


def test_cvat_uploader_imports():
    res = subprocess.run([sys.executable, "-c", "import src.cvat_uploader"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
