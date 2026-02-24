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
