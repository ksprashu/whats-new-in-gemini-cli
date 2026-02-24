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
from agents.changelog_agent import ChangelogAgent
from agents.github_agent import GitHubAgent
from agents.writer_agent import WriterAgent
from utils.storage import save_report

def test_single_feature():
    print("Testing single feature processing...")
    # Use a real example from the changelog we saw earlier
    feature = {
        "id": "v0.29.0_test_plan_mode",
        "version": "v0.29.0",
        "text": "Plan Mode: A new comprehensive planning capability with /plan, enter_plan_mode tool, and dedicated documentation",
        "pr_links": [
            "https://github.com/google-gemini/gemini-cli/pull/17698",
            "https://github.com/google-gemini/gemini-cli/pull/18324"
        ]
    }

    github_agent = GitHubAgent()
    writer_agent = WriterAgent()

    github_context = []
    for pr_url in feature["pr_links"]:
        print(f"Fetching PR: {pr_url}")
        pr_data = github_agent.fetch_pr_data(pr_url)
        github_context.append(pr_data)

    print("Generating report...")
    report = writer_agent.generate_report(feature["text"], github_context)
    
    save_report(feature["id"], feature["text"][:100], report, feature["version"])
    print(f"Report saved: reports/{feature['id']}.md")

if __name__ == "__main__":
    test_single_feature()
