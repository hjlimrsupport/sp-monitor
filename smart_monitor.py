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
DAILY_STATE_FILE = Path("site_state_daily.json")
SUMMARY_FILE = Path("site_summary.json")
REPORT_META_FILE = Path("site_report_meta.json")
HISTORY_FILE = Path("monitoring_history.json")

SITEMAP_URL = "https://www.splashtop.co.jp/wp-sitemap.xml"
DYNAMIC_PATHS = ['/news', '/achievements', '/products-service', '/knowhow', '/blog', '/corporate-blog']
NEW_ONLY_PATHS = ['/achievements', '/knowhow']

def fetch_sitemap_urls(url, visited_sitemaps=None):
    if visited_sitemaps is None:
        visited_sitemaps = set()
    
    if url in visited_sitemaps:
        return []
    visited_sitemaps.add(url)
    
    print(f"📡 Processing sitemap: {url}")
    all_urls = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, timeout=15, headers=headers)
        if response.status_code == 200:
            content = response.text
            
            # 1. Check for Sitemap Index entries
            sub_sitemaps = re.findall(r'<sitemap>.*?<loc>(.*?)</loc>.*?</sitemap>', content, re.DOTALL)
            if not sub_sitemaps:
                # Fallback for simpler index formats
                if '<sitemapindex' in content:
                    sub_sitemaps = re.findall(r'<loc>(.*?)</loc>', content)
            
            for sub in sub_sitemaps:
                if sub.endswith('.xml'):
                    all_urls.extend(fetch_sitemap_urls(sub, visited_sitemaps))
            
            # 2. Extract Page URLs (Ignoring lastmod, priority etc.)
            # We look specifically for <loc> inside <url> tags
            urls = re.findall(r'<url>.*?<loc>(.*?)</loc>.*?</url>', content, re.DOTALL)
            if not urls:
                # Support plain lists of <loc> if <url> tags are missing
                urls = re.findall(r'<loc>(.*?)</loc>', content)
            
            for u in urls:
                u = u.strip().split('#')[0].rstrip('/')
                if u.startswith("http") and not u.endswith('.xml'):
                    all_urls.append(u)
                    
    except Exception as e:
        print(f"⚠️ Sitemap fetch failed ({url}): {e}")
    
    return list(set(all_urls))

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
        response = requests.get(url, timeout=12, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- DEEP DISCOVERY: Extract internal links to find unlisted pages ---
            base_domain = "https://www.splashtop.co.jp"
            discovered_links = []
            if any(path in url for path in DYNAMIC_PATHS):
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(base_domain, href).split('#')[0].rstrip('/')
                    if full_url.startswith(base_domain) and not any(ext in full_url.lower() for ext in ['.pdf', '.zip', '.jpg', '.png']):
                        if not should_ignore(full_url):
                            discovered_links.append(full_url)

            title = soup.title.string.strip() if soup.title else "No Title"
            if not title: title = "No Title"
            
            meta_desc = soup.find("meta", {"name": "description"})
            description = meta_desc["content"].strip() if meta_desc and "content" in meta_desc.attrs else "No Description"
            
            cleaned_content = soup.get_text()
            content_hash = hashlib.sha256(cleaned_content.encode('utf-8')).hexdigest()
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "hash": content_hash,
                "status": "success",
                "links": list(set(discovered_links)) # Share discovered links back
            }
        elif response.status_code == 404:
            return {"url": url, "status": "404"}
    except Exception as e:
        print(f"⚠️ Fetch failed for {url}: {e}")
    return {"url": url, "status": "error"}

def run_targeted_monitor():
    # 1. Initialize Daily Baseline Stability
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_run_time = datetime.now().isoformat()
    
    # Load Master State (The most recent known state)
    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            master_state = json.load(f)
    else:
        master_state = {}

    # Load Daily Baseline (Used to calculate the report diff for "Today")
    if not DAILY_STATE_FILE.exists():
        # First time ever run or manually deleted
        with DAILY_STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(master_state, f, indent=4, ensure_ascii=False)
        baseline_state = master_state
        last_report_date = today_str # Set to today to avoid re-triggering baseline update in this run
    else:
        # Check the date of the last report to see if we need to rotate baseline
        last_report_date = ""
        if REPORT_META_FILE.exists():
            try:
                with REPORT_META_FILE.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
                    last_report_date = meta.get("curr_time", "").split("T")[0]
            except: pass
        
        if last_report_date != today_str:
            print(f"📆 New Day Detected ({today_str}). Rotating daily baseline...")
            with DAILY_STATE_FILE.open("w", encoding="utf-8") as f:
                json.dump(master_state, f, indent=4, ensure_ascii=False)
            baseline_state = master_state
        else:
            print(f"📆 Same Day Run. Comparing against today's initial baseline.")
            with DAILY_STATE_FILE.open("r", encoding="utf-8") as f:
                baseline_state = json.load(f)

    # 2. XML Differential Discovery
    sitemap_urls = fetch_sitemap_urls(SITEMAP_URL)
    if not sitemap_urls:
        print("❌ Could not fetch sitemap. Aborting.")
        return False

    # Normalize sitemap URLs
    sitemap_set = set(normalize_url(u) for u in sitemap_urls if not should_ignore(u))
    master_set = set(master_state.keys())
    baseline_set = set(baseline_state.keys())

    # Differential Detection
    new_urls_since_baseline = sitemap_set - baseline_set
    deleted_urls_since_baseline = baseline_set - sitemap_set
    stable_urls = sitemap_set & baseline_set

    # Determine which URLs to actually FETCH
    # We fetch:
    # - New URLs (to get title/description)
    # - Priority URLs (to check for content modifications)
    priority_urls = [u for u in stable_urls if is_dynamic(u)]
    urls_to_fetch = sorted(list(new_urls_since_baseline | set(priority_urls)))
    
    print(f"📊 Sitemap Stats: {len(sitemap_set)} URLs found.")
    print(f"🔎 Scanning {len(urls_to_fetch)} priority/new URLs for changes...")

    # 3. Concurrent Content Fetching
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(get_page_info, url): url for url in urls_to_fetch}
        completed = 0
        for future in as_completed(future_to_url):
            completed += 1
            info = future.result()
            results.append(info)
            if completed % 20 == 0 or completed == len(urls_to_fetch):
                print(f"📊 Progress: {completed}/{len(urls_to_fetch)} tasks finished.")

    url_to_info = {res["url"]: res for res in results}
    
    # --- DEEP SYNC: Merge links found in HTML with our sitemap list ---
    final_url_set = sitemap_set.copy()
    for res in results:
        if "links" in res:
            for link in res["links"]:
                if link not in final_url_set:
                    print(f"🕵️ Deep Discovery Found: {link}")
                    final_url_set.add(link)
                    # For these newly found links, we'll mark them as 'new'
                    # and they will be processed in the next run's fetch list.

    # 4. Generate Summary and Update States
    summary_data = []
    new_master_state = master_state.copy()
    
    # Process all URLs in the final merged set
    for url in final_url_set:
        status = "stable"
        info = url_to_info.get(url)
        
        # Detect Status based on Baseline
        if url in new_urls_since_baseline or (url in final_url_set and url not in sitemap_set):
            status = "new"
            print(f"🆕 NEW: {url}")
        elif url in priority_urls and info and info["status"] == "success":
            # Check for modification against baseline
            old_hash = baseline_state.get(url, {}).get("hash")
            if old_hash and info["hash"] != old_hash:
                if not is_new_only(url):
                    status = "changed"
                    print(f"📝 CHANGED: {url}")
        
        # Determine metadata to display
        if info and info["status"] == "success":
            # Update master state with latest content info
            new_master_state[url] = {
                "hash": info["hash"],
                "title": info["title"],
                "description": info["description"],
                "last_checked": current_run_time
            }
            display_info = info
        else:
            # Fallback to baseline or master data for existing URLs we didn't fetch
            display_info = master_state.get(url, baseline_state.get(url, {}))

        summary_data.append({
            "url": url,
            "title": display_info.get("title", "No Title"),
            "description": display_info.get("description", "No Description"),
            "status": status,
            "baseline_date": baseline_state.get(url, {}).get("last_checked", "Initial"),
            "last_checked": current_run_time
        })

    # Add missing/deleted pages to report
    for url in deleted_urls_since_baseline:
        old_info = baseline_state.get(url, {})
        summary_data.append({
            "url": url,
            "title": old_info.get("title", "Unknown"),
            "description": "No longer in sitemap.",
            "status": "deleted",
            "baseline_date": old_info.get("last_checked", "Initial"),
            "last_checked": current_run_time
        })
        if url in new_master_state:
            del new_master_state[url]

    # 5. Save Results
    report_meta = {
        "prev_count": len(baseline_state),
        "curr_count": len(sitemap_set),
        "prev_time": min([v.get("last_checked", "") for v in baseline_state.values()] + [current_run_time]) if baseline_state else "Initial",
        "curr_time": current_run_time,
        "total_checked": len(urls_to_fetch)
    }

    with SUMMARY_FILE.open("w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(new_master_state, f, indent=4, ensure_ascii=False)
    with REPORT_META_FILE.open("w", encoding="utf-8") as f:
        json.dump(report_meta, f, indent=4, ensure_ascii=False)

    # 6. Append to History
    history = []
    if HISTORY_FILE.exists():
        try:
            with HISTORY_FILE.open("r", encoding="utf-8") as f:
                history = json.load(f)
        except: pass
    
    # Calculate counts and details for history
    h_new_urls = list(new_urls_since_baseline)
    h_del_urls = list(deleted_urls_since_baseline)
    h_chg_count = sum(1 for item in summary_data if item["status"] == "changed")
    
    history.append({
        "timestamp": current_run_time,
        "date": today_str,
        "total_count": len(sitemap_set),
        "new_count": len(h_new_urls),
        "deleted_count": len(h_del_urls),
        "changed_count": h_chg_count,
        "new_details": h_new_urls,
        "deleted_details": h_del_urls
    })
    
    # Keep last 2000 entries (approx. 5.5 years of daily scans)
    history = history[-2000:]
    
    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

    # Update site_structure.json for external visibility
    with STRUCTURE_FILE.open("w", encoding="utf-8") as f:
        json.dump({url: 2 for url in sitemap_set}, f, indent=4, ensure_ascii=False)

    print(f"\n✨ Monitoring complete. XML Diff found {len(new_urls_since_baseline)} new and {len(deleted_urls_since_baseline)} deleted pages.")
    return True

if __name__ == "__main__":
    run_targeted_monitor()
