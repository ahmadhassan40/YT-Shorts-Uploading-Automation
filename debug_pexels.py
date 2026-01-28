import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_pexels")

API_KEY = "UmSOeCVpk5P2YuWho1vjHUESsv6RRv4O4JygamgGvHWyB2m37wnndKJi"
QUERY = "internet"

def test_query(q, orientation=None, size=None):
    print(f"\n--- Testing Query: '{q}' (Orientation: {orientation}, Size: {size}) ---")
    headers = {"Authorization": API_KEY}
    params = {
        "query": q,
        "per_page": 5
    }
    if orientation:
        params["orientation"] = orientation
    if size:
        params["size"] = size
    
    url = "https://api.pexels.com/videos/search"
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        print(f"Total Results: {data.get('total_results', 0)}")
        print(f"Videos Found: {len(data.get('videos', []))}")
    except Exception as e:
        print(f"Error: {e}")

def test_pexels():
    # Test strict vs loose parameters for failing queries
    test_query("rome", orientation="portrait", size="medium")
    test_query("rome", orientation="portrait", size=None)
    test_query("rome", orientation=None, size=None)
    
    test_query("internet", orientation="portrait", size="medium")
    test_query("internet", orientation=None, size=None)
    
    # Control group
    test_query("technology", orientation="portrait", size="medium")

if __name__ == "__main__":
    test_pexels()
