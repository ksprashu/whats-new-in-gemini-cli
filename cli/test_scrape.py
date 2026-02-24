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

import httpx
from bs4 import BeautifulSoup
import re

url = "https://geminicli.com/docs/changelogs/"
response = httpx.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

print("Extracting full changelog bullets...")
for elem in soup.find_all(string=re.compile(r'#\d+')):
    # Navigate up until we find a list item, paragraph, or div that likely contains the whole entry
    parent = elem.parent
    while parent and parent.name not in ['li', 'p', 'h3', 'h4'] and parent.name != 'body':
        parent = parent.parent
    
    if parent and parent.name != 'body':
        print(f"[{parent.name}]: {parent.get_text().strip()}")
    else:
        print(f"Failed to find reasonable parent for: {elem}")
