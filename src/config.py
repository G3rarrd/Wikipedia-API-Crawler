from typing import List, Dict, Final
from sentence_transformers import SentenceTransformer

HEADERS: List[Dict[str, str]] = [
    {
        "User-Agent": "MyScraper/1.0 (okiki98@example.com) ProjectName/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    },
    {
        "User-Agent": "AcademicResearchApp/3.4 (https://research.example.edu/project; research-team@example.edu)",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    },
    {
        "User-Agent": "AlgorithmTesting/1.0 (aydoelerichard218@gmail.com)",
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "AlgorithmTesting/1.0 (olaitanJ238@gmail.com)",
        "Accept-Encoding": "gzip",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "contentTestingObservation/1.0 (titlayoWunmi76@gmail.com)",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip",
    },
]

# MODEL : SentenceTransformer = None
MODEL : SentenceTransformer = SentenceTransformer("all-MiniLM-L6-v2")

URL : str = "https://en.wikipedia.org"

API_URL : Final[str] = "https://en.wikipedia.org/w/api.php"