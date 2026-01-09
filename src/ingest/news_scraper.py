import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import time
from urllib.parse import urljoin, urlparse

OUTPUT_DIR = "data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_article(url):
    """Scrape a single article"""
    print(f"  Scraping: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Get title
    title = soup.find('h1')
    title_text = title.get_text().strip() if title else "No title"

    # Get article content
    paragraphs = soup.find_all("p")
    text = "\n".join(p.get_text() for p in paragraphs)

    return {
        "url": url,
        "title": title_text,
        "scraped_at": datetime.utcnow().isoformat(),
        "content": text.strip()
    }

def find_article_links(homepage_url, max_links=5):
    """Find article links from a homepage"""
    print(f"\nFinding articles on: {homepage_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(homepage_url, timeout=10, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all links
    links = []
    base_domain = urlparse(homepage_url).netloc
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(homepage_url, href)
        
        # Only include links from the same domain
        if urlparse(full_url).netloc == base_domain:
            # Filter for likely article URLs (customize per site)
            if any(keyword in full_url.lower() for keyword in ['blog', 'news', 'article', 'post', '202']):
                if full_url not in links:
                    links.append(full_url)
                    if len(links) >= max_links:
                        break
    
    print(f"  Found {len(links)} article links")
    return links

if __name__ == "__main__":
    print("Starting improved news scraper...")
    
    # Sites to scrape
    sites = [
        {
            "name": "Microsoft 365 Blog",
            "homepage": "https://www.microsoft.com/en-us/microsoft-365/blog/",
            "max_articles": 3
        },
        {
            "name": "Salesforce News",
            "homepage": "https://www.salesforce.com/news/",
            "max_articles": 3
        }
    ]

    all_articles = []

    for site in sites:
        print(f"\n{'='*60}")
        print(f"Processing: {site['name']}")
        print('='*60)
        
        try:
            # Get article links
            article_links = find_article_links(site['homepage'], max_links=site['max_articles'])
            
            # Scrape each article
            for link in article_links:
                try:
                    article = scrape_article(link)
                    all_articles.append(article)
                    time.sleep(1)  # Be polite, don't hammer servers
                except Exception as e:
                    print(f"  ✗ Failed to scrape article: {e}")
                    
        except Exception as e:
            print(f"✗ Failed to process {site['name']}: {e}")

    # Save results
    output_path = os.path.join(OUTPUT_DIR, "articles.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✓ Saved {len(all_articles)} articles to {output_path}")
    print('='*60)
    
    # Show summary
    if all_articles:
        print("\nArticles scraped:")
        for i, article in enumerate(all_articles, 1):
            print(f"{i}. {article['title'][:60]}... ({len(article['content'])} chars)")