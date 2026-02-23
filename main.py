import sys
from agents.changelog_agent import ChangelogAgent
from agents.github_agent import GitHubAgent
from agents.writer_agent import WriterAgent
from utils.storage import is_processed, save_report
import argparse

def run_update():
    print("Starting update check...")
    changelog_agent = ChangelogAgent()
    github_agent = GitHubAgent()
    writer_agent = WriterAgent()

    features = changelog_agent.get_latest_features()
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
        report = writer_agent.generate_report(feature["text"], github_context)
        
        # Save to storage
        save_report(feature_id, feature["text"][:100], report, feature["version"])
        print(f"  Report saved for {feature_id}")

    print("Update check complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="What's New in Gemini CLI - Orchestrator")
    parser.add_argument("--check", action="store_true", help="Check for updates and generate reports")
    args = parser.parse_args()

    if args.check:
        run_update()
    else:
        parser.print_help()
