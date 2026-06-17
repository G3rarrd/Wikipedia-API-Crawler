def token_similarity(a : str, b: str) -> float:
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())

    if not a_tokens or not b_tokens:
        return 0.0
    
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)

import difflib

def diff_similarity(a : str, b : str):
    return difflib.SequenceMatcher(None, a, b).ratio()
