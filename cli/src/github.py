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
import httpx
from pydantic import BaseModel
from typing import List, Optional

class PRComment(BaseModel):
    author: str
    body: str

class PRDetails(BaseModel):
    number: int
    title: str
    body: Optional[str] = ""
    comments: List[PRComment] = []

class GitHubExtractor:
    def __init__(self, token: Optional[str] = None, repo: str = "google-gemini/gemini-cli"):
        self.repo = repo
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def get_pr_details(self, pr_number: int) -> PRDetails:
        """
        Fetches the PR's main body/title and its associated issue comments.
        """
        base_url = f"https://api.github.com/repos/{self.repo}"
        
        with httpx.Client(headers=self.headers) as client:
            # 1. Fetch main PR info
            pr_resp = client.get(f"{base_url}/pulls/{pr_number}")
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()
            
            title = pr_data.get("title", "")
            body = pr_data.get("body", "") or ""
            
            # 2. Fetch comments (Issue comments API covers PR general comments)
            comments_resp = client.get(f"{base_url}/issues/{pr_number}/comments")
            comments_resp.raise_for_status()
            comments_data = comments_resp.json()
            
            comments = []
            for comment in comments_data:
                author = comment.get("user", {}).get("login", "unknown")
                c_body = comment.get("body", "")
                if c_body:
                    comments.append(PRComment(author=author, body=c_body))
                    
            return PRDetails(
                number=pr_number,
                title=title,
                body=body,
                comments=comments
            )

    def format_pr_for_llm(self, pr_details: PRDetails) -> str:
        """
        Formats the fetched PR details into a single markdown string 
        optimized for Gemini to read and synthesize.
        """
        output = [
            f"# PR {pr_details.number}: {pr_details.title}",
            "## Description",
            pr_details.body,
            "",
            "## Discussion & Context"
        ]
        
        if not pr_details.comments:
            output.append("No comments.")
        else:
            for comment in pr_details.comments:
                output.append(f"### @{comment.author} commented:")
                output.append(comment.body)
                output.append("---")
                
        return "\n".join(output)
