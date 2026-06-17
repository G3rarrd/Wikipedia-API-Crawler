import httpx
from typing import List, Dict, Any, Set
import asyncio
import random
from itertools import cycle
from config import HEADERS, API_URL


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

EXCLUDED_PATTERNS = (
    "List of ",         # list pages
    "Lists of ",        # plural list pages
    "Index of ",        # index pages
    "Outline of ",      # outline pages
    "Glossary of ",     # glossary pages
    "History of ",      # debatable — remove if you want these
)

def is_valid_article(title: str) -> bool:
    # filter namespaces and shortcuts
    if any(title.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    # filter list/index pages
    if any(title.startswith(pattern) for pattern in EXCLUDED_PATTERNS):
        return False
    # filter single character or very short titles (usually shortcuts)
    if len(title) <= 2:
        return False
    return True

async def extract_forwardlink_texts(
    client: httpx.AsyncClient,
    title: str,
    meeting,
) -> List[str]:

    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "titles": title,
        "prop": "links",
        "pllimit": "max",
    }

    results: Set[str] = set()

    try:
        while True:
            # print("Forwardlinks ongoing")
            headers = next(ua_cycle)
            resp = await client.get(API_URL, headers=headers, params=params)
            resp.raise_for_status()

            data: Dict[str, Any] = resp.json()

            pages = data.get("query", {}).get("pages", [])

            if not pages:
                return []

            page = pages[0]

            if page.get("missing"):
                return []

            for link in page.get("links", []):
                link_title = link.get("title", None)

                if link_title and is_valid_article(link_title):
                    results.add(link_title)

            # handle pagination
            if "continue" not in data or meeting["node"] is not None:
                # print("forwardlinks stopped")
                break

            params.update(data["continue"])

            # await asyncio.sleep(random.uniform(1, 1.5))

    except httpx.HTTPError as e:
        print(f"[HTTP ERROR] {e}")
        return []
    except Exception as e:
        print(f"[PARSE ERROR] {e}")
        return []

    return results


import httpx
from typing import List, Dict, Any


async def extract_backlink_texts(
    client: httpx.AsyncClient,
    title: str,
    meeting,
) -> List[str]:

    params = {
        "action": "query",
        "format": "json",
        "list": "backlinks",
        "bltitle": title,
        "bllimit": "max",
        "blnamespace": 0,
    }

    results: List[str] = []

    try:
        while True:
            # print("processing backlinks")
            headers = next(ua_cycle)
            
            resp = await client.get(API_URL, headers=headers, params=params)
            resp.raise_for_status()

            data: Dict[str, Any] = resp.json()

            backlinks = data.get("query", {}).get("backlinks", [])

            for link in backlinks:
                link_title = link.get("title", None)

                if link_title and is_valid_article(link_title):
                    results.append(link_title)

            if "continue" not in data or meeting["node"] is not None :
                break

            params.update(data["continue"])

    except httpx.HTTPError as e:
        print(f"[HTTP ERROR] {e}")
        return []
    except Exception as e:
        print(f"[PARSE ERROR] {e}")
        return []

    return results