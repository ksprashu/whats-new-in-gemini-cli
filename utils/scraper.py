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
from selectolax.lexbor import LexborHTMLParser
import hashlib
from pathlib import Path
import logging

CACHE_DIR = Path(".cache/scraper")

def fetch_html(url: str, use_cache: bool = True) -> str:
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        cache_file = CACHE_DIR / f"{url_hash}.html"
        if cache_file.exists():
            return cache_file.read_text(encoding='utf-8')

    with httpx.Client() as client:
        try:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            text = response.text
            if use_cache:
                cache_file.write_text(text, encoding='utf-8')
            return text
        except httpx.HTTPStatusError as e:
            logging.warning(f"Failed to fetch {url}: {e}")
            return ""
        except httpx.RequestError as e:
            logging.warning(f"Request error for {url}: {e}")
            return ""

def parse_html(html: str) -> LexborHTMLParser:
    return LexborHTMLParser(html)
