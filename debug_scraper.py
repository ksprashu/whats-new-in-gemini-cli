import re
from utils.scraper import fetch_html, parse_html

url = "https://geminicli.com/docs/changelogs/"
html = fetch_html(url)
parser = parse_html(html)

for h2 in parser.css("h2"):
    header_text = h2.text().strip()
    version_match = re.search(r"Announcements: (v[\d\.]+) - ([\d-]+)", header_text)
    if version_match:
        print(f"Header: {header_text}")
        print(f"Grandparent html: {h2.parent.parent.html}")
        break
