from asyncio import Lock, Queue
import asyncio
import httpx
from typing import Dict, List, Tuple, Optional
import traceback
from utils.link_extractor import extract_links
from config import HEADERS
import random
from utils.url_transformers import text_to_url
from utils.path_builder import build_path

class BFS:
    def __init__(self, start_title : str, end_title : str, num_workers : int):
        self.start_title = start_title
        self.end_title = end_title
        self.num_workers = num_workers

        self.lock : Lock = Lock()
        self.visited : Dict[str, List[str]]= {}
        self.meeting: Dict[str, Optional[str]] = {"node": None}
        self.parent_map: Dict[str, str] = {}
        self.queue: Queue = Queue()
        self.client: Optional[httpx.AsyncClient] = None

        self.poison_pills = num_workers # to end the workers

    async def _worker(self, name : str):
        while True:
            cur_url, cur_text, prev_text = await self.queue.get()

            if self.meeting["node"] is not None or cur_url is None:
                self.queue.task_done()
                return
            try:
                async with self.lock:
                    if cur_text in self.visited:
                        continue

                    if self.meeting["node"] is not None:
                        continue

                    self.parent_map.setdefault(cur_text, prev_text)
                    self.visited[cur_text] = []

                print(f"{name} | {cur_text} | {prev_text}")

                url_texts_found = await extract_links(self.client, cur_url)

                if url_texts_found == []:
                    continue

                if self.meeting["node"] is not None:
                    continue

                async with self.lock:
                    self.visited[cur_text] = url_texts_found

                match_found = False
                for url, text in url_texts_found:
                    if text.lower() == self.end_title.lower():
                        match_found = True
                        break

                    if text in self.visited:
                        continue

                    await self.queue.put((url, text, cur_text))

                if match_found:
                    async with self.lock:
                        self.meeting["node"] = self.end_title
                        self.parent_map[self.end_title] = cur_text

                        # winning worker sends poison pills only
                        for _ in range(self.num_workers):
                            self.queue.put_nowait((float("inf"), (None, None, None)))

                        print(f"🎯 Target Found!!!")

            except Exception as e:
                print(f"Error in {name}: {e}")
                traceback.print_exc()

            finally:
                self.queue.task_done()

    async def run(self):
        async with httpx.AsyncClient(headers=random.choice(HEADERS)) as client:
            self.client = client
            start_url : str = text_to_url(self.start_title)

            await self.queue.put((start_url, self.start_title, None))

            workers = [asyncio.create_task(self._worker(f"Worker {i}"))
                       for i in range(self.num_workers)]
            
            print("Started")
            await asyncio.gather(*workers)

            if self.meeting["node"] is None:
                print("No Path Found")
                return []
            
            path = build_path(self.parent_map, self.end_title)[::-1]

            print(" -> ".join(path))

            return path
            
