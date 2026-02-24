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

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import subprocess

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

from pydantic import BaseModel

class SyncRequest(BaseModel):
    fetch_more: bool = False

@app.post("/api/sync")
def sync_changelog(request: Request, sync_req: SyncRequest = SyncRequest()):
    verify_admin(request)
    # Call the main script to sync
    cmd = ["python", "main.py", "--check"]
    if sync_req.fetch_more:
        cmd.append("--fetch-more")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {"status": "success", "output": result.stdout, "error": result.stderr}

# Mount static files. We will create a static folder in the next step.
os.makedirs("static", exist_ok=True)
# Try to mount, but allow failure if not present yet during dev testing
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
