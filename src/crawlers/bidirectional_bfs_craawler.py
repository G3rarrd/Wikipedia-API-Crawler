from utils.page_link_texts_extraction import extract_forwardlink_texts, extract_backlink_texts
from utils.url_transformers import get_normalized_title
from typing import Dict, List, Optional
from asyncio import Lock, Queue, Task
from abc import ABC, abstractmethod
import asyncio
import httpx
import random
import traceback
from config import HEADERS


class BidirectionalBFS:
    def __init__(
        self,
        start_title: str,
        end_title: str,
        num_forward_workers: int,
        num_backward_workers: int,
    ):
        self.start_title = start_title
        self.end_title = end_title
        self.num_forward_workers = num_forward_workers
        self.num_backward_workers = num_backward_workers

        self.meeting: Dict[str, Optional[str]] = {"node": None}
        self.lock: Lock = Lock()

        self.forward_queue: Queue = Queue()
        self.backward_queue: Queue = Queue()

        self.forward_visited: Dict[str, List[str]] = {}
        self.backward_visited: Dict[str, List[str]] = {}

        self.forward_parent_map: Dict[str, str] = {}
        self.backward_parent_map: Dict[str, str] = {}

        self.poison_pills = max(num_forward_workers, num_backward_workers)
        self.client: Optional[httpx.AsyncClient] = None

    async def _worker(
        self,
        name: str,
        main_queue: Queue,
        other_queue: Queue,
        main_visited: Dict[str, List[str]],
        other_visited: Dict[str, List[str]],
        parent_map: Dict[str, str],
        extract_func,
    ):
        while True:
            node = await main_queue.get()

            if self.meeting["node"] is not None or node is None:
                main_queue.task_done()
                return

            cur_title, prev_title = node

            print(f"{name} | {node} | {main_queue.qsize()} | {other_queue.qsize()}")

            try:
                async with self.lock:
                    if self.meeting["node"] is not None:
                        continue

                    if cur_title in other_visited:
                        self.meeting["node"] = cur_title
                        parent_map.setdefault(cur_title, prev_title)

                        # send poison pills while still holding the lock —
                        # guarantees only ONE worker ever sends them
                        for _ in range(self.poison_pills):
                            main_queue.put_nowait(None)
                            other_queue.put_nowait(None)

                        print(f"🎯 Target Found!!! {name} | {cur_title}")
                        continue

                    already_attempted = cur_title in main_visited
                    if not already_attempted:
                        parent_map.setdefault(cur_title, prev_title)
                        main_visited[cur_title] = []  # mark in-progress

                if already_attempted:
                    continue  # nothing new to fetch, already handled

                titles_found = await extract_func(self.client, cur_title, self.meeting)

                if self.meeting["node"] is not None:
                    continue

                found_target = None
                new_titles = []
                for title in titles_found:
                    if title in other_visited:
                        found_target = title
                        break
                    new_titles.append(title)

                async with self.lock:
                    if self.meeting["node"] is not None:
                        continue

                    main_visited[cur_title] = titles_found

                    if found_target is not None:
                        self.meeting["node"] = found_target
                        parent_map.setdefault(found_target, cur_title)
                        for _ in range(self.poison_pills):
                            main_queue.put_nowait(None)
                            other_queue.put_nowait(None)
                        print(f"🎯 Target Found!!! {name} | {found_target}")
                    else:
                        for t in new_titles:
                            if t not in main_visited:
                                main_queue.put_nowait((t, cur_title))

            except Exception as e:
                print(f"Error in {name}: {e}")
                traceback.print_exc()
            finally:
                main_queue.task_done()

    async def run(self) -> Optional[List[str]]:
        async with httpx.AsyncClient(headers=random.choice(HEADERS)) as client:
            self.client = client

            root_title = await get_normalized_title(client, self.start_title)
            target_title = await get_normalized_title(client, self.end_title)

            await self.forward_queue.put((root_title, None))
            await self.backward_queue.put((target_title, None))

            forward_tasks = [
                asyncio.create_task(self._worker(
                    f"Forward Worker {i + 1}",
                    self.forward_queue, self.backward_queue,
                    self.forward_visited, self.backward_visited,
                    self.forward_parent_map,
                    extract_forwardlink_texts,
                ))
                for i in range(self.num_forward_workers)
            ]

            backward_tasks = [
                asyncio.create_task(self._worker(
                    f"Backward Worker {i + 1}",
                    self.backward_queue, self.forward_queue,
                    self.backward_visited, self.forward_visited,
                    self.backward_parent_map,
                    extract_backlink_texts,
                ))
                for i in range(self.num_backward_workers)
            ]

            await asyncio.gather(*forward_tasks, *backward_tasks)

        if self.meeting["node"] is None:
            print("No path found.")
            return None

        forward_path = (self.forward_parent_map, self.meeting["node"])[::-1]
        backward_path = (self.backward_parent_map, self.meeting["node"])[1:]

        full_path = forward_path + backward_path

        print(" -> ".join(full_path))
        return full_path