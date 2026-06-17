from config import URL
from urllib.parse import quote, urlparse
import httpx
from config import URL, API_URL

def text_to_url(title: str) -> str:
    return URL + "/wiki/" + quote(title.replace(" ", "_"))

def url_to_text(url: str) -> str:
    from urllib.parse import unquote
    path = urlparse(url).path          # /wiki/AC%2FDC
    title = path.replace("/wiki/", "") # AC%2FDC
    return unquote(title).replace("_", " ")  # AC/DC'

async def get_normalized_title(client: httpx.AsyncClient, title: str) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": title,
        "prop": "mainpage"  # Lightweight property to avoid downloading page body/links
    }

    resp = await client.get(API_URL, params=params)
    data = resp.json()

    query_data = data.get("query", {})
    normalized_list = query_data.get("normalized", [])

    if normalized_list:
        return normalized_list[0]["to"]
    
    return title