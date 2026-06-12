from asyncio import Lock, Queue
import httpx
from typing import Dict, List, Tuple, Optional
import traceback
from page_titles_extraction import extract_page_titles_async



def display_path(nodes : Dict[str, str], title : str):
    path : List[str] = []
    while title != None:
        path.append(title)
        title = nodes[title]
    print(' -> '.join(path[::-1]))
    return path[::-1]



async def worker(
        name : str, 
        url : str, 
        lock : Lock,
        client, title_queue : Queue,
        visited_titles : Dict[str, List[str]],
        isCompleted : Dict[str, bool],
        target_title : str,
        found_nodes : Dict[str, str]
    ):

    while True:
        if isCompleted["state"] == True:
            break

        node: Tuple[str, str] = await title_queue.get()

        cur_title : Optional[str] = node[0]
        prev_title : Optional[str] = node[1]
        print(f"{name} | {node} | {title_queue.qsize()}")
        if node is None:
            title_queue.task_done()
            break

        try:
            async with lock:
                if cur_title in visited_titles:
                    continue

                found_nodes[cur_title] = prev_title
                visited_titles[cur_title] = []

            titles_found = await extract_page_titles_async(url, client, cur_title)

            new_titles = []
            async with lock:
                if isCompleted["state"]:
                    continue

                visited_titles[cur_title] = titles_found

                for found_title in titles_found:
                    if found_title.lower() == target_title.lower():
                        found_nodes[found_title] = cur_title
                        isCompleted["state"] = True

                        print(f"🎯 Target Found!!! Path {display_path(found_nodes, found_title)} ")
                        break
                    
                    if found_title not in visited_titles:
                        new_titles.append(found_title)
                
            for t in new_titles:
                await title_queue.put([t, cur_title])

        except Exception as e:
            print(f"Error Found in {name}: {e}")
            traceback.print_exc()

        finally:
            title_queue.task_done()

                    

