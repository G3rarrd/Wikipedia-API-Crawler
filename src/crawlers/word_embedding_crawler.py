import httpx
import random
import asyncio
import traceback
from config import MODEL, HEADERS
from abc import ABC, abstractmethod
from utils.path_builder import build_path
from utils.similarity import diff_similarity
from asyncio import Lock, PriorityQueue
from asyncio import Lock, PriorityQueue
from typing import Dict, List, Optional
from utils.link_extractor import extract_links
from sentence_transformers.util import cos_sim
from utils.page_link_texts_extraction import extract_forwardlink_texts
from utils.url_transformers import url_to_text, text_to_url, get_normalized_title

class BaseWordEmbeddingBFS(ABC):
    def __init__(
            self,
            start_title: str,
            end_title: str,
            num_workers: int,
    ):
        self.start_title = start_title
        self.end_title = end_title
        self.num_workers = num_workers

        self.lock: Lock = Lock()
        self.heap_queue: PriorityQueue = PriorityQueue()
        self.visited_titles: Dict[str, List[str]] = {}
        self.parent_map: Dict[str, str] = {}
        self.meeting: Dict[str, Optional[str]] = {"node": None}
        self.target_embedding = None
        self.client: Optional[httpx.AsyncClient] = None

    async def get_embedding_scores(self, links_found: list[tuple[str, str]]):
        """links_found is list of (text, url) tuples."""
        if not links_found:
            return []

        texts = [text for _, text in links_found]
        titles_embedding = await asyncio.to_thread(MODEL.encode, texts)
        scores = cos_sim(self.target_embedding, titles_embedding)[0]

        return [
            ( url, text, 0.9 * score.item() + 0.1 * diff_similarity(text, self.end_title))
            for score, (url, text) in zip(scores, links_found)
        ]
    
    async def _worker(self, name: str):
        while True:
            cur_score, (cur_url, cur_text, prev_title) = await self.heap_queue.get()

            if self.meeting["node"] is not None or cur_score == float("inf"):
                self.heap_queue.task_done()
                return
            
            try:
                async with self.lock:
                    if cur_text in self.visited_titles:
                        continue

                    if self.meeting["node"] is not None:
                        continue

                    self.parent_map.setdefault(cur_text, prev_title)
                    self.visited_titles[cur_text] = []  # mark in-progress

                print(f"{name} | {cur_text} | {prev_title} | {cur_score}")

                texts_links_found = await self.fetch_links(cur_url, cur_text)

                if not texts_links_found:
                    continue

                text_url_scores = await self.get_embedding_scores(texts_links_found)

                if self.meeting["node"] is not None:
                    continue
                
                # For Safe insertion to the dictionary
                async with self.lock:
                    self.visited_titles[cur_text] = texts_links_found

                found_match = False
                for  url, text, score in text_url_scores:
                    if text.lower() == self.end_title.lower():
                        found_match = True
                        break

                    inverted_score = 1 - score # For max heap

                    if text in self.visited_titles:
                        continue

                    await self.heap_queue.put((inverted_score, (url, text, cur_text)))

                if found_match:
                    async with self.lock:
                        if self.meeting["node"] is None:
                            self.meeting["node"] = self.end_title
                            self.parent_map[self.end_title] = cur_text
                            self.visited_titles[cur_text] = texts_links_found

                    # winning worker sends poison pills
                    for _ in range(self.num_workers):
                        await self.heap_queue.put((float("inf"), (None, None, None)))

                    print(f"🎯 Target Found!!!")

            except Exception as e:
                print(f"Error in {name}: {e}")
                traceback.print_exc()

            finally:
                self.heap_queue.task_done()

    async def run(self) -> List[str]:
        async with httpx.AsyncClient(headers=random.choice(HEADERS)) as client:
            self.client = client
            end_title = await self.normalize_title(self.end_title)
            root_title = await self.normalize_title(self.start_title)
            root_url = text_to_url(root_title)
            self.target_embedding = await asyncio.to_thread(MODEL.encode, end_title)

            await self.heap_queue.put((0, (root_url, root_title, None)))

            tasks = [
                asyncio.create_task(self._worker(f"Worker {i}"))
                for i in range(self.num_workers)
            ]

            print("Started")

            await asyncio.gather(*tasks)

        if self.meeting["Node"] is None:
            print("No Path Found")
            return []

        path = build_path(self.parent_map, self.end_title)[::-1]

        print(" -> ".join(path))

        return path

    async def normalize_title(self, title: str) -> str:
        """Override if normalization needed (API version uses get_normalized_title)."""
        return title

class APIWordEmbeddingBFS(BaseWordEmbeddingBFS):
    async def fetch_links(self, cur_url: str, cur_text : str) -> List[str]:
        texts_found = await extract_forwardlink_texts(self.client, cur_text, self.meeting)
        return [(text_to_url(text), text) for text in texts_found]

    async def normalize_title(self, title: str) -> str:
        return await get_normalized_title(self.client, title)

class URLWordEmbeddingBFS(BaseWordEmbeddingBFS):
    async def fetch_links(self, cur_url: str, cur_text :str):
        links_texts_found = await extract_links(self.client, cur_url)
        return [(link, text) for link, text in links_texts_found]