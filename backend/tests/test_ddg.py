from duckduckgo_search import DDGS
import json

try:
    print("Attempting search...")
    with DDGS() as ddgs:
        results = list(ddgs.images("labeled diagram of eukaryotic cell", max_results=1))
    print(f"Results found: {len(results)}")
    if results:
        print("First image:", results[0]['image'])
except Exception as e:
    print(f"Error: {e}")
