import httpx

async def extract_page_titles_async(url : str, client: httpx.AsyncClient, title : str):
    links_params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",  # Keeps the JSON structure clean and flat
        "titles": title,
        "prop": "links",
        "pllimit": "max"       # Get the maximum number of links allowed per page
    }
    try:
        resp = await client.get(url, params=links_params)
        data = resp.json()

        pages = data["query"]["pages"]

        
        if not pages or pages[0].get("missing"):
            return []
        
        page_links = pages[0].get("links", [])

        return [link["title"] for link in page_links]
    except Exception as e:
        return []