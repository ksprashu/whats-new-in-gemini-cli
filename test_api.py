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

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, mock_open
from api import app

client = TestClient(app)

@patch("api.get_reports")
def test_list_reports(mock_get_reports):
    # mock_get_reports.return_value now needs valid 'version' properties for proper sorting
    mock_get_reports.return_value = {
        "1": {"title": "A", "status": "Done", "version": "v1.0.0"},
        "2": {"title": "B", "status": "Pending", "version": "v2.0.0"}
    }
    response = client.get("/api/reports")
    assert response.status_code == 200
    # Expected reverse order of insertion/version
    assert response.json() == [
        {"id": "2", "title": "B", "status": "Pending", "version": "v2.0.0"},
        {"id": "1", "title": "A", "status": "Done", "version": "v1.0.0"}
    ]

@patch("os.path.exists")
@patch("api.get_reports")
def test_get_report_success(mock_get_reports, mock_exists):
    mock_get_reports.return_value = {
        "1": {"title": "A", "status": "Done", "file": "/dummy/file.md"}
    }
    mock_exists.return_value = True
    
    with patch("builtins.open", mock_open(read_data="Markdown Content")):
        response = client.get("/api/reports/1")
        assert response.status_code == 200
        assert response.json() == {
            "id": "1",
            "title": "A",
            "status": "Done",
            "content": "Markdown Content",
            "file": "/dummy/file.md"
        }

@patch("api.get_reports")
def test_get_report_not_found(mock_get_reports):
    mock_get_reports.return_value = {}
    response = client.get("/api/reports/1")
    assert response.status_code == 404
    assert response.json() == {"detail": "Report not found"}

@patch("os.path.exists")
@patch("api.get_reports")
def test_get_report_file_missing(mock_get_reports, mock_exists):
    mock_get_reports.return_value = {
        "1": {"title": "A", "status": "Done", "file": "/fake/path.md"}
    }
    mock_exists.return_value = False
    
    response = client.get("/api/reports/1")
    assert response.status_code == 404
    assert response.json() == {"detail": "Report file missing"}

@patch("api.mark_as_done")
def test_set_report_done(mock_mark_as_done):
    response = client.post("/api/reports/1/done")
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    mock_mark_as_done.assert_called_once_with("1")

@patch("api.subprocess.run")
def test_sync_changelog_success(mock_run):
    mock_result = MagicMock()
    mock_result.stdout = "Sync success!"
    mock_result.stderr = ""
    mock_run.return_value = mock_result
    
    response = client.post("/api/sync")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "output": "Sync success!", "error": ""}
    mock_run.assert_called_once_with(["python", "main.py", "--check"], capture_output=True, text=True)
