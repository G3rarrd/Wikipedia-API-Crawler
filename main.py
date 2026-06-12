import requests
from typing import Optional, Final, List, Dict, Tuple
import json
import random
import httpx
import asyncio
from graph_generator import generate_graph
from worker import worker, Lock, Queue


URL : Final[str] = "https://en.wikipedia.org/w/api.php"

HEADERS : List[Dict[str, str]] = [
{
    "User-Agent": "MyDataScienceApp/1.0 (olawunmi97l@gmail.com)",
    "Accept-Encoding": "gzip"
},]


params = {
    "action": "query",
    "format": "json",
    "titles": "Python (programming language)",
    "prop": "extracts",
    "exintro": True,
    "explaintext": True,
}


def choose_header_random() -> List[Dict[str, str]]:
    return random.choice(HEADERS)

async def get_normalized_title(client: httpx.AsyncClient, title: str) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": title,
        "prop": "mainpage"  # Lightweight property to avoid downloading page body/links
    }

    resp = await client.get(URL, params=params)
    data = resp.json()

    query_data = data.get("query", {})
    normalized_list = query_data.get("normalized", [])

    if normalized_list:
        return normalized_list[0]["to"]
    
    return title

def extract_page_links(title : str):
    links_params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",  # Keeps the JSON structure clean and flat
        "titles": title,
        "prop": "links",
        "pllimit": "max"       # Get the maximum number of links allowed per page
    }
    headers : Dict[str, str] = choose_header_random() 
    resp = requests.get(URL, headers=headers, params=links_params)
    data = resp.json()
    print(json.dumps(data, indent=4))

    pages = data["query"]["pages"]
    page_links = pages[0].get("links", [])
    link_titles = [link["title"] for link in page_links]

    return link_titles

async def main():
    num_workers : int = 10
    task_done_state = {"state" : False}

    lock : Lock = Lock()
    title_queue : Queue = Queue()
    visited_titles : Dict = {}
    found_path : Dict[str, str] = {}

    async with httpx.AsyncClient(headers=choose_header_random()) as client:
        
        root_title : str = await get_normalized_title(client, "london")
        target_title : str = await get_normalized_title(client, "john elton")
        
        await title_queue.put([root_title, None])
        
        workers = [asyncio.create_task(worker(
            f"Worker {i}", URL, lock, client,title_queue,
            visited_titles, task_done_state, target_title, found_path))
            for i in range(num_workers)
        ]
        
        await asyncio.gather(*workers)
        # generate_graph(visited_titles)
        # print(json.dumps(visited_titles, indent=4))

if "__main__" == __name__:
    asyncio.run(main()) 



