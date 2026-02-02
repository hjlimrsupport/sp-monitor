import json
from pathlib import Path
from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    try:
        parsed = urlparse(url)
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
        return normalized.rstrip('/')
    except:
        return url

def cleanup_json(filename):
    file_path = Path(filename)
    if not file_path.exists():
        return
    
    with file_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_data = {}
    if isinstance(data, dict):
        for url, val in data.items():
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                continue 
                
            norm = normalize_url(url)
            if norm not in new_data:
                new_data[norm] = val
        
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)
        print(f"Cleaned {filename}: {len(data)} -> {len(new_data)} entries.")
    
    elif isinstance(data, list):
        seen_urls = set()
        new_list = []
        for item in data:
            url = item.get("url")
            if url:
                norm = normalize_url(url)
                if norm not in seen_urls:
                    seen_urls.add(norm)
                    item["url"] = norm
                    new_list.append(item)
        
        with file_path.open('w', encoding='utf-8') as f:
            json.dump(new_list, f, indent=4, ensure_ascii=False)
        print(f"Cleaned {filename} (list): {len(data)} -> {len(new_list)} entries.")

def run_cleanup():
    cleanup_json("site_structure.json")
    cleanup_json("site_state.json")
    cleanup_json("site_summary.json")
    print("Cleanup complete.")

if __name__ == "__main__":
    run_cleanup()
