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

import sys
from agents.changelog_agent import ChangelogAgent
from agents.github_agent import GitHubAgent
from agents.writer_agent import WriterAgent
from utils.storage import is_processed, save_report
import argparse

def run_update(fetch_more=False):
    print("Starting update check...")
    changelog_agent = ChangelogAgent()
    github_agent = GitHubAgent()
    writer_agent = WriterAgent()

    features = changelog_agent.get_latest_features(fetch_more=fetch_more)
    print(f"Found {len(features)} features in changelog.")

    for feature in features:
        feature_id = feature["id"]
        if is_processed(feature_id):
            print(f"Feature {feature_id} already processed. Skipping.")
            continue

        print(f"Processing new feature: {feature['text'][:50]}...")
        
        # Gather GitHub context
        github_context = []
        for pr_url in feature["pr_links"]:
            print(f"  Fetching PR: {pr_url}")
            pr_data = github_agent.fetch_pr_data(pr_url)
            github_context.append(pr_data)
            
            # Fetch linked issues for even more context
            for issue_url in pr_data.get("linked_issues", []):
                if "github.com" in issue_url and "/issues/" in issue_url:
                    print(f"    Fetching Issue: {issue_url}")
                    issue_data = github_agent.fetch_issue_data(issue_url)
                    github_context.append(issue_data)

        # Generate report
        print("  Generating report with Gemini...")
        report, feature_status = writer_agent.generate_report(feature["text"], github_context)
        
        # Save to storage
        save_report(feature_id, feature["text"], report, feature["version"], feature["date"], feature_status)
        print(f"  Report saved for {feature_id}")

    print("Update check complete.")

def run_reformat():
    print("Starting reformatting of existing reports...")
    from utils.storage import get_reports, update_metadata
    from pathlib import Path
    
    writer_agent = WriterAgent()
    reports_metadata = get_reports()
    
    count = 0
    total = len(reports_metadata)
    
    for feature_id, metadata in reports_metadata.items():
        file_path = Path(metadata["file"])
        if not file_path.exists():
            print(f"  Warning: File {file_path} not found for {feature_id}. Skipping.")
            continue
            
        print(f"  [{count+1}/{total}] Reformatting {feature_id}...")
        with open(file_path, "r") as f:
            old_content = f.read()
            
        new_content, feature_status = writer_agent.reformat_report(old_content)
        
        with open(file_path, "w") as f:
            f.write(new_content)
            
        update_metadata(feature_id, {"feature_status": feature_status})
            
        count += 1
        
    print(f"Successfully reformatted {count} reports.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="What's New in Gemini CLI - Orchestrator")
    parser.add_argument("--check", action="store_true", help="Check for updates and generate reports")
    parser.add_argument("--fetch-more", action="store_true", help="Fetch the next 10 remaining items from the changelog")
    parser.add_argument("--reformat-existing", action="store_true", help="Reformat all existing reports using the new prompt structure")
    args = parser.parse_args()

    if args.check:
        run_update(fetch_more=args.fetch_more)
    elif args.reformat_existing:
        run_reformat()
    else:
        parser.print_help()
