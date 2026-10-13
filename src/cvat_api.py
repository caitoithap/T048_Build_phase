import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import requests

class CVATApiClient:
    """
    CVAT REST API Client for Live Data Ingestion.
    Connects directly to CVAT Server (Self-hosted or app.cvat.ai),
    fetches Task/Job annotations, Reviewer Issues, and Frame images.
    """
    def __init__(self, server_url="https://app.cvat.ai", auth_token="", username="", password=""):
        self.server_url = server_url.rstrip("/")
        self.auth_token = auth_token
        self.username = username
        self.password = password
        self.session = requests.Session()
        
        if auth_token:
            self.session.headers.update({"Authorization": f"Token {auth_token}"})
        elif username and password:
            self.session.auth = (username, password)

    def test_connection(self):
        """
        Tests connection to CVAT server.
        """
        try:
            url = f"{self.server_url}/api/server/about"
            resp = self.session.get(url, timeout=5)
            if resp.status_code == 200:
                return True, "Kết nối CVAT Server thành công!"
            else:
                return False, f"Lỗi HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"Không thể kết nối đến {self.server_url}: {str(e)}"

    def get_task_details(self, task_id):
        """
        Fetches Task metadata from CVAT REST API.
        """
        url = f"{self.server_url}/api/tasks/{task_id}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"⚠️ Fetch task {task_id} failed: {resp.status_code}")
                return None
        except Exception as e:
            print(f"⚠️ Task detail exception: {e}")
            return None

    def fetch_task_annotations_xml(self, task_id, save_path):
        """
        Downloads annotations in CVAT XML format and saves to save_path.
        """
        url = f"{self.server_url}/api/tasks/{task_id}/annotations"
        params = {"format": "CVAT 1.1", "action": "download"}
        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"📥 CVAT Annotations downloaded to: {save_path}")
                return str(save_path)
            else:
                print(f"⚠️ Download annotations HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"⚠️ Download exception: {e}")
            return None

    def fetch_task_issues(self, task_id):
        """
        Fetches Reviewer Issues and Comments for a specific CVAT Task.
        Returns a list of issues with comments.
        """
        url = f"{self.server_url}/api/issues"
        params = {"task_id": task_id}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", data) if isinstance(data, dict) else data
                return results
            return []
        except Exception as e:
            print(f"⚠️ Fetch issues exception: {e}")
            return []

    def mock_fetch_task_data(self, task_id, sample_xml_path, output_dir):
        """
        Mock / Simulation Mode when live CVAT server is offline.
        Simulates fetching Task metadata, XML annotations, and Reviewer Issues.
        """
        print(f"🔄 Simulating CVAT API Data Ingestion for Task #{task_id}...")
        issues = [
            {
                "id": 101,
                "task_id": task_id,
                "frame": 0,
                "position": [120, 150, 200, 250],
                "owner": {"username": "Mentor_An"},
                "comments": [
                    {"message": "Xe ô tô màu bạc phía xa bị bỏ sót Bbox, hãy bổ sung nhãn."},
                    {"message": "Đã gắn bổ sung nhưng Bbox quá sát mép ảnh."}
                ],
                "created_date": "2026-10-06T10:15:00Z",
                "resolved": False
            },
            {
                "id": 102,
                "task_id": task_id,
                "frame": 2,
                "position": [450, 300, 520, 410],
                "owner": {"username": "Mentor_Thành"},
                "comments": [
                    {"message": "Bbox này nhầm lẫn giữa Truck và Bus. Cần sửa lại class."}
                ],
                "created_date": "2026-10-06T11:20:00Z",
                "resolved": False
            }
        ]
        
        task_meta = {
            "id": task_id,
            "name": f"VinUni Road Detection Task #{task_id}",
            "status": "in progress",
            "owner": {"username": "admin"},
            "assignee": {"username": "Nguyễn Trọng Hùng"},
            "segment_size": 10,
            "image_quality": 70,
            "issues_count": len(issues)
        }
        
        return task_meta, sample_xml_path, issues
