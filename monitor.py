import requests
import hashlib
import json
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("site_state.json")
STRUCTURE_FILE = Path("site_structure.json")

def get_content_hash(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code == 200:
            content = response.text
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def monitor():
    if not STRUCTURE_FILE.exists():
        print("Structure file not found. Please run crawler first.")
        return None

    with STRUCTURE_FILE.open("r", encoding="utf-8") as f:
        structure = json.load(f)

    # structure is a dict of {url: depth}
    urls = sorted(structure.keys())

    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            old_state = json.load(f)
    else:
        old_state = {}

    new_state = {}
    changes = []

    print(f"Monitoring {len(urls)} URLs...")
    for url in urls:
        print(f"Checking {url}...")
        current_hash = get_content_hash(url)
        if current_hash:
            new_state[url] = {
                "hash": current_hash,
                "last_checked": datetime.now().isoformat()
            }
            
            if url in old_state:
                if old_state[url]["hash"] != current_hash:
                    changes.append(f"CHANGED: {url}")
            else:
                changes.append(f"NEW: {url}")
        else:
            new_state[url] = old_state.get(url, {"hash": None, "last_checked": None})
            if url in old_state:
                changes.append(f"FAILED: {url}")

    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(new_state, f, indent=4, ensure_ascii=False)

    if changes:
        print("\n--- Changes Detected ---")
        for change in changes:
            print(change)
    else:
        print("\nNo changes detected.")
    
    return changes

if __name__ == "__main__":
    monitor()
