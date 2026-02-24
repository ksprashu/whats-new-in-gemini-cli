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
import pytest
from unittest.mock import MagicMock
from src.github import GitHubExtractor, PRDetails, PRComment
import httpx

def test_github_extractor_formats_pr_details():
    extractor = GitHubExtractor(token="dummy", repo="fake/repo")
    
    # Manually build PRDetails object to test format_pr_for_llm
    details = PRDetails(
        number=17698,
        title="Plan Mode: A new capability",
        body="This PR implements `/plan` mode which adds multi-step reasoning capabilities.",
        comments=[
            PRComment(author="Adib234", body="We should also update the docs!"),
            PRComment(author="reviewer", body="Looks great, merging.")
        ]
    )
    
    formatted = extractor.format_pr_for_llm(details)
    
    assert "# PR 17698: Plan Mode: A new capability" in formatted
    assert "This PR implements `/plan` mode" in formatted
    assert "### @Adib234 commented:" in formatted
    assert "We should also update the docs!" in formatted

def test_github_extractor_get_pr_details(mocker):
    extractor = GitHubExtractor(token="dummy", repo="fake/repo")
    
    # Create mock response object representing the httpx.Response
    mock_client = MagicMock()
    
    pr_resp = MagicMock()
    pr_resp.json.return_value = {"title": "Test PR", "body": "PR Content Body"}
    
    comments_resp = MagicMock()
    comments_resp.json.return_value = [
        {"user": {"login": "testuser"}, "body": "Comment 1"}
    ]
    
    # Map the URLs to specific response mocks
    def get_side_effect(url):
        if url.endswith("/pulls/123"):
            return pr_resp
        elif url.endswith("/issues/123/comments"):
            return comments_resp
        raise ValueError(f"Unexpected url: {url}")
        
    mock_client.get.side_effect = get_side_effect
    
    # Mock httpx.Client context manager
    mocker.patch('httpx.Client.__enter__', return_value=mock_client)
    
    details = extractor.get_pr_details(123)
    
    assert details.number == 123
    assert details.title == "Test PR"
    assert details.body == "PR Content Body"
    assert len(details.comments) == 1
    assert details.comments[0].author == "testuser"
    assert details.comments[0].body == "Comment 1"
