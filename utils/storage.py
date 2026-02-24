# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from pathlib import Path
from typing import Dict, Optional

# Check if we are in cloud mode
STORAGE_MODE = os.environ.get("STORAGE_MODE", "local")
GCS_BUCKET = os.environ.get("GCS_BUCKET")

# Local settings
REPORTS_DIR = Path("reports")
METADATA_FILE = REPORTS_DIR / "metadata.json"

# Cloud settings
db = None
storage_client = None
if STORAGE_MODE == "cloud":
    from google.cloud import firestore
    from google.cloud import storage
    db = firestore.Client()
    storage_client = storage.Client()


def init_storage():
    if STORAGE_MODE != "cloud":
        REPORTS_DIR.mkdir(exist_ok=True)
        if not METADATA_FILE.exists():
            with open(METADATA_FILE, "w") as f:
                json.dump({}, f)


def save_report(id: str, title: str, content: str, version: str, date: str, feature_status: str = "Available"):
    init_storage()
    
    if STORAGE_MODE == "cloud":
        file_path = f"gs://{GCS_BUCKET}/reports/{id}.md"
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"reports/{id}.md")
        blob.upload_from_string(content, content_type="text/markdown")
    else:
        file_path = str(REPORTS_DIR / f"{id}.md")
        with open(file_path, "w") as f:
            f.write(content)
    
    update_metadata(id, {
        "title": title,
        "version": version,
        "date": date,
        "status": "Pending",
        "feature_status": feature_status,
        "file": file_path
    })


def update_metadata(id: str, data: Dict):
    init_storage()
    if STORAGE_MODE == "cloud":
        # Write to Firestore
        doc_ref = db.collection("gemini-cli-reports").document(id)
        doc_ref.set(data, merge=True)
    else:
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
        
        if id not in metadata:
            metadata[id] = {}
        metadata[id].update(data)
        
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)


def get_reports() -> Dict:
    init_storage()
    if STORAGE_MODE == "cloud":
        reports = {}
        docs = db.collection("gemini-cli-reports").stream()
        for doc in docs:
            reports[doc.id] = doc.to_dict()
        return reports
    else:
        with open(METADATA_FILE, "r") as f:
            return json.load(f)

def get_report_content(report_id: str, file_path: str) -> Optional[str]:
    """Retrieve markdown content abstracting Local FS or GCS logic."""
    if STORAGE_MODE == "cloud":
        try:
            bucket = storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"reports/{report_id}.md")
            return blob.download_as_text()
        except Exception:
            return None
    else:
        # Local
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return f.read()
        return None

def mark_as_done(id: str):
    update_metadata(id, {"status": "Done"})


def is_processed(id: str) -> bool:
    return id in get_reports()
