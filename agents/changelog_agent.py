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

import re
import hashlib
from typing import List, Dict
from utils.scraper import fetch_html, parse_html
from utils.storage import get_reports

CHANGELOG_URL = "https://geminicli.com/docs/changelogs/"

class ChangelogAgent:
    def __init__(self):
        self.url = CHANGELOG_URL

    def get_latest_features(self, fetch_more: bool = False) -> List[Dict]:
        """
        Scrapes the changelog and returns a list of features with their PR links.
        If fetch_more is True, grabs the 10 items *older* than the oldest processed item.
        Otherwise, grabs the latest items up to 10, stopping at the first processed item.
        """
        html = fetch_html(self.url, use_cache=False)
        parser = parse_html(html)
        
        all_features = []
        processed_reports = get_reports()
        
        # Find all h2 headers that match "Announcements: v..."
        for h2 in parser.css("h2"):
            header_text = h2.text().strip()
            version_match = re.search(r"Announcements: (v[\d\.]+) - ([\d-]+)", header_text)
            if version_match:
                version = version_match.group(1)
                date = version_match.group(2)
                
                next_node = h2.parent.next
                while next_node and next_node.tag != "ul":
                    next_node = next_node.next
                
                if next_node and next_node.tag == "ul":
                    for li in next_node.css("li"):
                        feature_text = li.text().strip().replace("\n", " ")
                        pr_links = []
                        for a in li.css("a"):
                            href = a.attributes.get("href", "")
                            if "github.com" in href and "/pull/" in href:
                                pr_links.append(href)
                        
                        feature_hash = hashlib.sha256(feature_text.encode('utf-8')).hexdigest()[:8]
                        feature_id = f"{version}_{feature_hash}"
                        
                        all_features.append({
                            "version": version,
                            "date": date,
                            "text": feature_text,
                            "pr_links": pr_links,
                            "id": feature_id
                        })

        new_features = []
        if not fetch_more:
            # Fetch Latest: Take items until we hit a processed one, max 10
            for f in all_features:
                if f["id"] in processed_reports:
                    break
                new_features.append(f)
                if len(new_features) >= 10:
                    break
        else:
            # Fetch More: Skip any already-processed items and take the next 10 unprocessed items
            for f in all_features:
                if f["id"] in processed_reports:
                    continue
                new_features.append(f)
                if len(new_features) >= 10:
                    break
        return new_features

if __name__ == "__main__":
    agent = ChangelogAgent()
    features = agent.get_latest_features()
    for f in features[:3]:
        print(f"Version: {f['version']}, Text: {f['text'][:50]}..., PRs: {f['pr_links']}")
