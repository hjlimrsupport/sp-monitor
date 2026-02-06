import requests
from bs4 import BeautifulSoup
import json
import os

STRUCTURE_FILE = "site_structure.json"
SUMMARY_FILE = "site_summary.json"

def get_page_metadata(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else "No Title"
            meta_desc = soup.find("meta", {"name": "description"})
            description = meta_desc["content"].strip() if meta_desc and "content" in meta_desc.attrs else "No Description"
            return title, description
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return "Error", "Error"

def generate_summary():
    if not os.path.exists(STRUCTURE_FILE):
        print("Structure file not found.")
        return

    with open(STRUCTURE_FILE, "r", encoding="utf-8") as f:
        structure = json.load(f)

    # Filter for important pages (Depth 0 and 1)
    important_urls = [url for url, depth in structure.items() if depth <= 1]
    
    summary_data = []
    print(f"Fetching metadata for {len(important_urls)} important URLs...")
    
    for url in important_urls:
        print(f"Processing: {url}")
        title, desc = get_page_metadata(url)
        summary_data.append({
            "url": url,
            "title": title,
            "description": desc
        })

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=4, ensure_ascii=False)

    print(f"\nSummary generated in {SUMMARY_FILE}")

if __name__ == "__main__":
    generate_summary()
