import requests
import hashlib
import json
import os
from datetime import datetime

STATE_FILE = "site_state.json"
STRUCTURE_FILE = "site_structure.json"

def get_content_hash(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # We can use text or just a hash of the text to save space
            # Strip some dynamic parts if necessary (like timestamps, but let's keep it simple first)
            content = response.text
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def monitor():
    if not os.path.exists(STRUCTURE_FILE):
        print("Structure file not found. Please run crawler.py first.")
        return

    with open(STRUCTURE_FILE, "r", encoding="utf-8") as f:
        structure = json.load(f)

    # structure is a dict of {url: depth}
    urls = sorted(structure.keys())

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
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

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_state, f, indent=4, ensure_ascii=False)

    if changes:
        print("\n--- Changes Detected ---")
        for change in changes:
            print(change)
    else:
        print("\nNo changes detected.")

if __name__ == "__main__":
    monitor()
