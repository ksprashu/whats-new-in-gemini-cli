import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import subprocess

from utils.storage import get_reports, mark_as_done

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

@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    reports = get_reports()
    if report_id not in reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    file_path = reports[report_id]["file"]
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
            return {
                "id": report_id,
                "content": content,
                "status": reports[report_id]["status"],
                **reports[report_id]
            }
    raise HTTPException(status_code=404, detail="Report file missing")

@app.post("/api/reports/{report_id}/done")
def set_report_done(report_id: str):
    mark_as_done(report_id)
    return {"status": "success"}

@app.post("/api/sync")
def sync_changelog():
    # Call the main script to sync
    result = subprocess.run(["python", "main.py", "--check"], capture_output=True, text=True)
    return {"status": "success", "output": result.stdout, "error": result.stderr}

# Mount static files. We will create a static folder in the next step.
os.makedirs("static", exist_ok=True)
# Try to mount, but allow failure if not present yet during dev testing
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
