from typing import List, Dict
from utils.scraper import fetch_html, parse_html

class GitHubAgent:
    def fetch_pr_data(self, pr_url: str) -> Dict:
        """
        Fetches the PR description and linked issues.
        """
        html = fetch_html(pr_url)
        parser = parse_html(html)
        
        # PR Title
        title = ""
        title_node = parser.css_first("h1.gh-header-title")
        if title_node:
            title = title_node.text().strip()
            
        # PR Description
        description = ""
        desc_node = parser.css_first("td.comment-body")
        if desc_node:
            description = desc_node.text().strip()
            
        # Linked Issues - GitHub often lists these in a specific sidebar or comment
        # For simplicity, we'll look for "Fixes #..." in the description
        # or links to /issues/
        linked_issues = []
        for a in parser.css("a"):
            href = a.attributes.get("href", "")
            if "google-gemini/gemini-cli/issues/" in href:
                if href.startswith("/"):
                    href = f"https://github.com{href}"
                linked_issues.append(href)
        
        return {
            "url": pr_url,
            "title": title,
            "description": description,
            "linked_issues": list(set(linked_issues))
        }

    def fetch_issue_data(self, issue_url: str) -> Dict:
        """
        Fetches the issue description.
        """
        html = fetch_html(issue_url)
        parser = parse_html(html)
        
        description = ""
        desc_node = parser.css_first("td.comment-body")
        if desc_node:
            description = desc_node.text().strip()
            
        return {
            "url": issue_url,
            "description": description
        }

if __name__ == "__main__":
    agent = GitHubAgent()
    data = agent.fetch_pr_data("https://github.com/google-gemini/gemini-cli/pull/17698")
    print(f"PR Title: {data['title']}")
    print(f"PR Description Snippet: {data['description'][:100]}...")
    print(f"Linked Issues: {data['linked_issues']}")
