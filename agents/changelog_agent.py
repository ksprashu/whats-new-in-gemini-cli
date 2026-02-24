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
from utils.storage import is_processed

CHANGELOG_URL = "https://geminicli.com/docs/changelogs/"

class ChangelogAgent:
    def __init__(self):
        self.url = CHANGELOG_URL

    def get_latest_features(self, fetch_more: bool = False) -> List[Dict]:
        """
        Scrapes the changelog and returns a list of features with their PR links.
        If fetch_more is True, skips all previously processed items and grabs the next 10.
        Otherwise, grabs the latest 10 items, stopping if an already processed item is found.
        """
        html = fetch_html(self.url)
        parser = parse_html(html)
        
        features = []
        skip_mode = fetch_more
        
        # Find all h2 headers that match "Announcements: v..."
        for h2 in parser.css("h2"):
            header_text = h2.text().strip()
            version_match = re.search(r"Announcements: (v[\d\.]+) - ([\d-]+)", header_text)
            if version_match:
                version = version_match.group(1)
                date = version_match.group(2)
                
                # The h2 is wrapped in a div. The ul is a sibling of that div.
                # In selectolax, we can find the next sibling of the parent.
                next_node = h2.parent.next
                while next_node and next_node.tag != "ul":
                    next_node = next_node.next
                
                if next_node and next_node.tag == "ul":
                    for li in next_node.css("li"):
                        feature_text = li.text().strip().replace("\n", " ")
                        # Extract PR links from the li
                        pr_links = []
                        for a in li.css("a"):
                            href = a.attributes.get("href", "")
                            if "github.com" in href and "/pull/" in href:
                                pr_links.append(href)
                        
                        feature_hash = hashlib.sha256(feature_text.encode('utf-8')).hexdigest()[:8]
                        feature_id = f"{version}_{feature_hash}"
                        
                        processed = is_processed(feature_id)
                        
                        if skip_mode:
                            if processed:
                                continue # Keep skipping until we find an unprocessed one
                            else:
                                skip_mode = False # Found the start of unprocessed items, stop skipping
                        else:
                            if processed and not fetch_more:
                                # Standard mode: stop at the first processed item
                                return features
                            elif processed and fetch_more:
                                # Defensive: should not hit this due to skip_mode, but just in case
                                continue

                        # If we reach here, we are not skipping and the item is not processed
                        features.append({
                            "version": version,
                            "date": date,
                            "text": feature_text,
                            "pr_links": pr_links,
                            "id": feature_id
                        })
                        
                        if len(features) >= 10:
                            return features
        
        return features

if __name__ == "__main__":
    agent = ChangelogAgent()
    features = agent.get_latest_features()
    for f in features[:3]:
        print(f"Version: {f['version']}, Text: {f['text'][:50]}..., PRs: {f['pr_links']}")
