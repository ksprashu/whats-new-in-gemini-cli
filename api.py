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

import logging
import os
import subprocess
import threading
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)
_sync_lock = threading.Lock()
SYNC_TIMEOUT_SECONDS = 300

app = FastAPI(title="What's New in Gemini CLI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_version(v_str):
    try:
        return [int(x) for x in v_str.lstrip("v").split(".")]
    except:
        return [0, 0, 0]

@app.get("/api/reports")
def list_reports():
    reports = get_reports()
    # Sort reports by version (descending) to show newest first
    reports_list = [{"id": rid, **data} for rid, data in reports.items()]
    reports_list.sort(key=lambda x: parse_version(x.get("version", "v0.0.0")), reverse=True)
    return reports_list

from utils.storage import get_reports, mark_as_done, get_report_content
from fastapi import Request

def verify_admin(request: Request):
    admin_key = os.environ.get("ADMIN_API_KEY")
    auth_header = request.headers.get("Authorization", "")
    if not admin_key or auth_header != f"Bearer {admin_key}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/api/reports/{report_id}")
def get_report(report_id: str, request: Request):
    reports = get_reports()
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    file_path = reports[report_id].get("file", "")
    content = get_report_content(report_id, file_path)
    
    if content is not None:
        # Server-Side Security Stripping
        admin_key = os.environ.get("ADMIN_API_KEY")
        auth_header = request.headers.get("Authorization", "")
        
        # If no admin key matches, we sever the admin section *before* sending the payload
        if not admin_key or auth_header != f"Bearer {admin_key}":
            admin_delimiter = "<!-- === ADMIN === -->"
            content = content.split(admin_delimiter)[0].strip()
            
        return {
            "id": report_id,
            "content": content,
            "status": reports[report_id].get("status", "Pending"),
            **reports[report_id]
        }
    raise HTTPException(status_code=404, detail="Report file missing")

@app.post("/api/reports/{report_id}/done")
def set_report_done(report_id: str, request: Request):
    verify_admin(request)
    mark_as_done(report_id)
    return {"status": "success"}

class SyncRequest(BaseModel):
    fetch_more: bool = False

@app.post("/api/sync")
def sync_changelog(request: Request, background_tasks: BackgroundTasks, sync_req: SyncRequest = SyncRequest()):
    verify_admin(request)
    if not _sync_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Synchronization is already in progress.")

    cmd = ["python", "main.py", "--check"]
    if sync_req.fetch_more:
        cmd.append("--fetch-more")

    def run_sync_cmd():
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=SYNC_TIMEOUT_SECONDS)
            if res.stdout:
                logger.info("Sync stdout: %s", res.stdout.strip())
            if res.returncode != 0:
                logger.error("Sync failed (exit %d): %s", res.returncode, res.stderr.strip())
            elif res.stderr:
                logger.warning("Sync stderr: %s", res.stderr.strip())
        except subprocess.TimeoutExpired:
            logger.error("Sync command timed out after %d seconds", SYNC_TIMEOUT_SECONDS)
        except Exception:
            logger.exception("Unexpected error running sync command")
        finally:
            _sync_lock.release()

    background_tasks.add_task(run_sync_cmd)
    return {"status": "success", "message": "Synchronization started in the background."}

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.isdir(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
