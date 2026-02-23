import re
import hashlib
from typing import List, Dict
from utils.scraper import fetch_html, parse_html
from utils.storage import is_processed

CHANGELOG_URL = "https://geminicli.com/docs/changelogs/"

class ChangelogAgent:
    def __init__(self):
        self.url = CHANGELOG_URL

    def get_latest_features(self) -> List[Dict]:
        """
        Scrapes the changelog and returns a list of features with their PR links.
        """
        html = fetch_html(self.url)
        parser = parse_html(html)
        
        features = []
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
                        
                        if is_processed(feature_id):
                            return features

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
