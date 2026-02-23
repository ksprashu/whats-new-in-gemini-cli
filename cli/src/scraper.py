import httpx
from bs4 import BeautifulSoup
import re
from pydantic import BaseModel
from typing import List

class ChangelogEntry(BaseModel):
    content: str
    pr_numbers: List[int]

def fetch_changelogs(url: str = "https://geminicli.com/docs/changelogs/") -> List[ChangelogEntry]:
    """
    Fetches the Gemini CLI changelog and extracts release notes and associated PR numbers.
    """
    response = httpx.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    entries = []
    
    # Let's find all text elements that match a PR pattern
    for elem in soup.find_all(string=re.compile(r'#\d+')):
        parent = elem.parent
        # Walk up the DOM to find the containing <li> or <p> element
        while parent and parent.name not in ['li', 'p'] and parent.name != 'body':
            parent = parent.parent
        
        if parent and parent.name in ['li', 'p']:
            # Replace newlines and excessive whitespace
            content = " ".join(parent.get_text(separator=' ').split()).strip()
            
            # Extract all PR numbers from this block of text
            pr_matches = re.findall(r'#(\d+)', content)
            prs = [int(pr) for pr in pr_matches]
            
            if prs:
                entry = ChangelogEntry(content=content, pr_numbers=prs)
                if entry not in entries:
                    entries.append(entry)

    return entries

if __name__ == "__main__":
    logs = fetch_changelogs()
    for log in logs[:3]:
        print("Content: " + log.content)
        print("PRs: " + str(log.pr_numbers))
        print("---")
