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

from bs4 import BeautifulSoup
from src.scraper import fetch_changelogs, ChangelogEntry

def test_fetch_changelogs_structure(mocker):
    mock_html = """
    <html>
        <body>
            <ul>
                <li>Plan Mode: A new feature (#17698 by @Adib234, #18324 by @jerop).</li>
                <li>Another fix without PR.</li>
                <li>Bugfix related to rendering (#18414).</li>
            </ul>
        </body>
    </html>
    """
    
    # Mock httpx.get
    class MockResponse:
        text = mock_html
        def raise_for_status(self):
            pass

    mocker.patch('httpx.get', return_value=MockResponse())
    
    entries = fetch_changelogs("http://mocked.url")
    
    assert len(entries) == 2
    assert entries[0].pr_numbers == [17698, 18324]
    assert "Plan Mode" in entries[0].content
    assert entries[1].pr_numbers == [18414]
    assert "Bugfix" in entries[1].content
