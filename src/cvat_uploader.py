import requests
import config

class CVATUploader:
    """
    REST API Client for authenticating with CVAT and uploading pre-annotations.
    """
    def __init__(self, server_url=config.CVAT_SERVER_URL, username=config.CVAT_USERNAME, password=config.CVAT_PASSWORD):
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def check_connection(self):
        """
        Verify if CVAT Server is reachable and credentials are valid.
        """
        url = f"{self.server_url}/api/users/self"
        try:
            resp = self.session.get(url, timeout=5)
            if resp.status_code == 200:
                user_info = resp.json()
                print(f"✅ Connected to CVAT Server as [{user_info.get('username')}]")
                return True
            else:
                print(f"⚠️ CVAT Connection Failed (HTTP {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            print(f"🌐 CVAT Server Offline or Unreachable at {self.server_url}: {e}")
            return False

    def list_tasks(self):
        """
        Fetch list of tasks from CVAT Server.
        """
        url = f"{self.server_url}/api/tasks"
        try:
            resp = self.session.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                tasks = data.get("results", [])
                print(f"📋 Found {len(tasks)} tasks on CVAT Server.")
                return tasks
            return []
        except Exception as e:
            print(f"❌ Error fetching tasks: {e}")
            return []

    def upload_annotations(self, task_id, xml_file_path, format_name="CVAT 1.1"):
        """
        Upload pre-annotation XML file to a specific CVAT Task ID.
        """
        url = f"{self.server_url}/api/tasks/{task_id}/annotations?format={requests.utils.quote(format_name)}&action=import"
        print(f"🚀 Uploading pre-annotation XML to CVAT Task #{task_id}...")

        try:
            with open(xml_file_path, "rb") as f:
                files = {"annotation_file": f}
                resp = self.session.put(url, files=files, timeout=30)

            if resp.status_code in [200, 201, 202]:
                print(f"🎉 SUCCESS! Pre-annotations uploaded to CVAT Task #{task_id}.")
                return True
            else:
                print(f"❌ Upload Failed (HTTP {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Upload Exception: {e}")
            return False
