from typing import Optional, Final, List, Dict, Tuple
import asyncio
# from graph_generator import generate_graph
from crawlers.bidirectional_bfs_craawler import BidirectionalBFS
from crawlers.word_embedding_crawler import APIWordEmbeddingBFS, URLWordEmbeddingBFS
from crawlers.bfs_crawler import BFS
from utils.url_transformers import url_to_text, text_to_url


async def main():
    # target of interest ["koffi annan"]
    start_link = "https://en.wikipedia.org/wiki/John_Cena"
    end_link =  "https://en.wikipedia.org/wiki/Reddit"
    start_title = url_to_text(start_link)
    end_title = url_to_text(end_link)

    # uses wikipedia links
    # print(f"From: {start_title} | to: {end_title}")
    # url_bfs = URLWordEmbeddingBFS(
    #     start_title=start_title,
    #     end_title=end_title,
    #     num_workers=12,
    # )
    # path = await url_bfs.run()

    # uses Wikipedia API
    # api_bfs = APIWordEmbeddingBFS(
    #     start_title=start_title,
    #     end_title=end_title,
    #     num_workers=10
    # )

    # path = await api_bfs.run()

    # bid_bfs = BidirectionalBFS(
    #     start_title=start_title,
    #     end_title=end_title,
    #     num_forward_workers=5,
    #     num_backward_workers=5
    # )

    # path : Optional[List[str]] = await bid_bfs.run()

    bfs = BFS(
        start_title=start_title, 
        end_title=end_title, 
        num_workers=15
        )
    
    path : Optional[List[str]] = await bfs.run()



if "__main__" == __name__:
    asyncio.run(main()) 



