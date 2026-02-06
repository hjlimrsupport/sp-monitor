import json
import os
from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    try:
        parsed = urlparse(url)
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return normalized.rstrip('/')
    except:
        return url

def cleanup_json(filename, is_state=False):
    if not os.path.exists(filename):
        return
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_data = {}
    if isinstance(data, dict):
        for url, val in data.items():
            norm = normalize_url(url)
            # If multiple versions exist, keep the one with more data or the first one
            if norm not in new_data:
                new_data[norm] = val
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)
        print(f"Cleaned {filename}: {len(data)} -> {len(new_data)} entries.")

if __name__ == "__main__":
    cleanup_json("site_structure.json")
    cleanup_json("site_state.json", is_state=True)
    print("Cleanup complete. Duplicates removed.")
