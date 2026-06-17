from typing import Dict, List, Tuple, Optional
def build_path(parent_map : Dict[str, str], start : str):
    path : List[str] = []
    cur = start
    while cur is not None:
        path.append(cur)
        cur = parent_map[cur]
    return path