import json
import os
from pathlib import Path
from typing import Dict, List, Optional

REPORTS_DIR = Path("reports")
METADATA_FILE = REPORTS_DIR / "metadata.json"

def init_storage():
    REPORTS_DIR.mkdir(exist_ok=True)
    if not METADATA_FILE.exists():
        with open(METADATA_FILE, "w") as f:
            json.dump({}, f)

def save_report(id: str, title: str, content: str, version: str):
    init_storage()
    file_path = REPORTS_DIR / f"{id}.md"
    with open(file_path, "w") as f:
        f.write(content)
    
    update_metadata(id, {
        "title": title,
        "version": version,
        "status": "Pending",
        "file": str(file_path)
    })

def update_metadata(id: str, data: Dict):
    init_storage()
    with open(METADATA_FILE, "r") as f:
        metadata = json.load(f)
    
    if id not in metadata:
        metadata[id] = {}
    
    metadata[id].update(data)
    
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

def get_reports() -> Dict:
    init_storage()
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

def mark_as_done(id: str):
    update_metadata(id, {"status": "Done"})

def is_processed(id: str) -> bool:
    return id in get_reports()
