import requests
from bs4 import BeautifulSoup
import json
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from urllib.parse import urljoin, urlparse, urlunparse
from pathlib import Path

# Files
STRUCTURE_FILE = Path("site_structure.json")
STATE_FILE = Path("site_state.json")
SUMMARY_FILE = Path("site_summary.json")
REPORT_META_FILE = Path("site_report_meta.json")

DYNAMIC_PATHS = ['/news', '/achievements', '/products-service', '/knowhow', '/blog']
NEW_ONLY_PATHS = ['/achievements', '/knowhow']

# Patterns to ignore for automatic discovery and monitoring
IGNORE_PATTERNS = [
    r'/page/\d+',    # Pagination
    r'/tag/',        # Tag pages
    r'/category/',   # Category pages
    r'/author/',     # Author pages
    r'\?search=',    # Search results
    r'/(201[0-9]|202[0-3])[0-1][0-9]', # Old news articles (YYYYMM)
    r'/(201[0-9]|202[0-3])/'           # Old news articles (YYYY/MM style)
]

def should_ignore(url):
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, url):
            return True
    return False

def is_dynamic(url):
    if should_ignore(url):
        return False
    return any(path in url for path in DYNAMIC_PATHS) or url == "https://www.splashtop.co.jp"

def is_new_only(url):
    return any(path in url for path in NEW_ONLY_PATHS)

def normalize_url(url):
    parsed = urlparse(url)
    # Strip query parameters and fragments
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return normalized.rstrip('/')

def get_page_info(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, timeout=8, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract links for auto-discovery
            base_url = "https://www.splashtop.co.jp"
            links = []
            for a in soup.find_all('a', href=True):
                full_url = urljoin(base_url, a['href'])
                norm_link = normalize_url(full_url)
                if norm_link.startswith(base_url) and not any(ext in norm_link.lower() for ext in ['.pdf', '.zip', '.jpg', '.png', '.jpeg']):
                    if not should_ignore(norm_link):
                        links.append(norm_link)

            # --- STABILITY REFINEMENT ---
            for noisy in soup.find_all(['script', 'style', 'meta', 'noscript', 'iframe']):
                noisy.decompose()
            for inp in soup.find_all('input', type='hidden'):
                if any(x in inp.get('name', '').lower() for x in ['token', 'csrf', 'nonce', 'timestamp']):
                    inp.decompose()
            
            title = soup.title.string.strip() if soup.title else "No Title"
            # Get description from original text because we decomposed meta tags above
            # Actually, we should get description before decomposing or use a separate soup
            desc_soup = BeautifulSoup(response.text, 'html.parser')
            meta_desc = desc_soup.find("meta", {"name": "description"})
            description = meta_desc["content"].strip() if meta_desc and "content" in meta_desc.attrs else "No Description"
            
            cleaned_content = soup.get_text()
            content_hash = hashlib.sha256(cleaned_content.encode('utf-8')).hexdigest()
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "hash": content_hash,
                "status": "success",
                "links": list(set(links))
            }
        elif response.status_code == 404:
            return {"url": url, "status": "404"}
    except Exception as e:
        pass
    return {"url": url, "status": "error"}

def run_targeted_monitor():
    if not STRUCTURE_FILE.exists():
        print("Structure file not found.")
        return False

    with STRUCTURE_FILE.open("r", encoding="utf-8") as f:
        structure = json.load(f)

    current_target_urls = []
    for url, depth in structure.items():
        if depth <= 1 or (depth == 2 and is_dynamic(url)):
            parsed = urlparse(url)
            if parsed.scheme in ['http', 'https']:
                current_target_urls.append(url)
    
    current_target_urls = sorted(list(set(current_target_urls)))

    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            old_state = json.load(f)
    else:
        old_state = {}

    summary_data = []
    new_state = {}
    old_urls_not_seen = set(old_state.keys())

    # Metadata for the report
    prev_count = len(old_state)
    prev_time = "Initial Run"
    if old_state:
        last_checks = [v.get("last_checked") for v in old_state.values() if v.get("last_checked")]
        if last_checks:
            prev_time = max(last_checks)

    print(f"🚀 Starting monitor for {len(current_target_urls)} URLs (Concurrent mode)...")
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(get_page_info, url): url for url in current_target_urls}
        completed = 0
        for future in as_completed(future_to_url):
            completed += 1
            info = future.result()
            results.append(info)
            if completed % 10 == 0 or completed == len(current_target_urls):
                print(f"📊 Progress: {completed}/{len(current_target_urls)} tasks finished.")

    url_to_info = {res["url"]: res for res in results}
    current_run_time = datetime.now().isoformat()
    
    # Discovery Logic
    discovered_any_new = False
    for res in results:
        if "links" in res:
            for link in res["links"]:
                if link not in structure and is_dynamic(link):
                    structure[link] = 2 # Register as Depth 2 for new dynamic finds
                    discovered_any_new = True
                    print(f"📡 DISCOVERED NEW LINK: {link}")

    if discovered_any_new:
        with STRUCTURE_FILE.open("w", encoding="utf-8") as f:
            json.dump(structure, f, indent=4, ensure_ascii=False)

    for url in current_target_urls:
        if url in old_urls_not_seen:
            old_urls_not_seen.remove(url)

        info = url_to_info.get(url, {"status": "error"})
        
        if info["status"] == "success":
            change_status = "stable"
            if url not in old_state:
                change_status = "new"
                print(f"🆕 NEW: {url}")
            elif old_state[url].get("hash") != info["hash"]:
                if is_new_only(url):
                    change_status = "stable"
                else:
                    change_status = "changed"
                    print(f"📝 CHANGED: {url}")

            summary_data.append({
                "url": url,
                "title": info["title"],
                "description": info["description"],
                "status": change_status,
                "baseline_date": old_state.get(url, {}).get("last_checked", prev_time),
                "last_checked": current_run_time
            })
            
            new_state[url] = {
                "hash": info["hash"],
                "title": info["title"],
                "description": info["description"],
                "last_checked": current_run_time
            }
        elif info["status"] == "404":
            summary_data.append({
                "url": url, "title": "Page Not Found", "description": "Removed (404).", "status": "deleted"
            })
        else:
            if url in old_state:
                new_state[url] = old_state[url]
            summary_data.append({
                "url": url, "title": "Error", "description": "Connection failed.", "status": "error"
            })

    for missing_url in old_urls_not_seen:
        summary_data.append({
            "url": missing_url, "title": old_state[missing_url].get("title", "Unknown"), "description": "No longer linked.", "status": "deleted"
        })

    # Save additional report metadata
    report_meta = {
        "prev_count": prev_count,
        "curr_count": len(current_target_urls),
        "prev_time": prev_time,
        "curr_time": current_run_time,
        "total_checked": len(current_target_urls)
    }

    with SUMMARY_FILE.open("w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(new_state, f, indent=4, ensure_ascii=False)
    with REPORT_META_FILE.open("w", encoding="utf-8") as f:
        json.dump(report_meta, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Monitoring complete. Report generated.")
    return True

if __name__ == "__main__":
    run_targeted_monitor()
