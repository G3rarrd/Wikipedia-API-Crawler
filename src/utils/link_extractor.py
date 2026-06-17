from config import URL, HEADERS
from lxml import html
from typing import Optional
from urllib.parse import urljoin, urlparse, ParseResult
import httpx
from httpx import Response
from itertools import cycle
from utils.url_transformers import url_to_text
import asyncio
import traceback

ua_cycle = cycle(HEADERS)

EXCLUDED_PREFIXES = (
    "Wikipedia:",
    "Talk:",
    "User:",
    "User talk:",
    "File:",
    "Help:",
    "Category:",
    "Template:",
    "Portal:",
    "Special:",
    "WP:",        # Wikipedia: shortcut
    "H:",         # Help: shortcut  <-- add this
    "MOS:",       # Manual of Style shortcut
    "P:",         # Portal: shortcut
    "T:",         # Template: shortcut
)

MAX_RETRIES = 4

def is_valid_article(title: str) -> bool:
    # filter namespaces and shortcuts
    if any(title.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return True

async def extract_links(client: httpx.AsyncClient, current_url: str) -> list[str]:
    for attempt in range(MAX_RETRIES):
        try:
            headers = next(ua_cycle)
            response = await client.get(current_url, headers=headers)
            
            if response.status_code != 200:
                print(f"HTTP {response.status_code} | {current_url}")
                return []
            
            tree = html.fromstring(response.content)
            anchors = tree.xpath("//div[contains(@id, 'bodyContent')]//a")

            results = []
            seen = set()

            for a in anchors:
                link = a.get("href")
                text = a.text_content().strip()
                if text in seen:
                    continue

                if text and link and link.startswith("/wiki/") and is_valid_article(text):
                    seen.add(text)
                    full_link : str = URL + link
                    results.append((full_link, text))

            return results
                

            return list({
                (URL + a.get("href"), a.text_content().strip())
                for a in anchors
                if a.text_content() and a.get("href") and a.get("href").startswith("/wiki/")
            })

        except httpx.ConnectTimeout:
            wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
            print(f"ConnectTimeout | attempt {attempt + 1}/{MAX_RETRIES} | retrying in {wait}s")
            await asyncio.sleep(wait)

        except Exception as e:
            print(f"Link Extraction Error | {__name__} | {e}")
            traceback.print_exc()
            return []
        
    print(f"Failed after {MAX_RETRIES} attempts | {current_url}")
    return []
