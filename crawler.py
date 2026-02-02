import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from pathlib import Path

class SplashtopCrawler:
    def __init__(self, base_url, max_depth=3):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.visited = {}
        self.structure = {}

    def is_internal(self, url):
        parsed = urlparse(url)
        return parsed.netloc == '' or parsed.netloc == self.domain

    def normalize_url(self, url):
        parsed = urlparse(url)
        # Remove fragment and query params for basic mapping
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if normalized.endswith('/'):
            normalized = normalized[:-1]
        return normalized

    def crawl(self, url, depth=0):
        if depth > self.max_depth:
            return None

        normalized_url = self.normalize_url(url)
        if normalized_url in self.visited and self.visited[normalized_url] <= depth:
            return self.visited[normalized_url]

        print(f"Crawling depth {depth}: {url}")
        self.visited[normalized_url] = depth

        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(url, href)
                
                if self.is_internal(full_url):
                    norm_child = self.normalize_url(full_url)
                    # Stay within domain and avoid certain file types
                    if not any(norm_child.lower().endswith(ext) for ext in ['.pdf', '.zip', '.exe', '.jpg', '.png', '.jpeg', '.gif']):
                        if norm_child not in self.visited or self.visited[norm_child] > depth + 1:
                            links.append(full_url)

            # Deduplicate and sort
            links = sorted(list(set(links)))
            
            children_structure = {}
            for link in links:
                res = self.crawl(link, depth + 1)
                if res is not None or depth + 1 <= self.max_depth:
                    children_structure[self.normalize_url(link)] = {}

            return children_structure

        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None

def start_crawl(base_url="https://www.splashtop.co.jp/", max_depth=2, output_file="site_structure.json"):
    crawler = SplashtopCrawler(base_url, max_depth=max_depth)
    crawler.crawl(base_url)
    
    output_path = Path(output_file)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(crawler.visited, f, indent=4, ensure_ascii=False)
    
    print(f"\nCrawl complete. Results saved to {output_file}")
    return crawler.visited

if __name__ == "__main__":
    start_crawl()
