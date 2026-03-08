"""News article scraper with retry support, structured logging, and type hints.

Run from project root:
    python -m src.ingest.news_scraper
"""

import json
import logging
import sys
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Ensure project root is importable when run as a script
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import config  # noqa: E402

logger = logging.getLogger(__name__)


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": config.user_agent})
    return session


def _get_with_retry(
    session: requests.Session,
    url: str,
    *,
    retries: int | None = None,
    timeout: int | None = None,
) -> requests.Response:
    """GET *url* with exponential back-off on failure."""
    retries = retries if retries is not None else config.max_retries
    timeout = timeout if timeout is not None else config.request_timeout

    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            if attempt == retries:
                raise
            wait = 2 ** attempt
            logger.warning(
                "Attempt %d/%d failed for %s: %s. Retrying in %ds…",
                attempt, retries, url, exc, wait,
            )
            time.sleep(wait)
    raise RuntimeError("Unreachable")  # pragma: no cover


# ── Core scraping ─────────────────────────────────────────────────────────────

def scrape_article(
    url: str,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Scrape a single article URL and return its structured data."""
    logger.info("Scraping: %s", url)
    session = session or _build_session()

    response = _get_with_retry(session, url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Strip boilerplate
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title_tag = soup.find("h1")
    title = title_tag.get_text(separator=" ").strip() if title_tag else "No title"

    # Prefer <article> body; fall back to all <p> tags
    article_body = soup.find("article") or soup
    paragraphs = article_body.find_all("p")
    content = "\n".join(
        p.get_text(separator=" ").strip()
        for p in paragraphs
        if p.get_text(strip=True)
    )

    if not content:
        logger.warning("No paragraph content found at %s", url)

    return {
        "url": url,
        "title": title,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "content": content,
        "word_count": len(content.split()),
    }


def find_article_links(
    homepage_url: str,
    session: requests.Session | None = None,
    max_links: int = 5,
    keywords: list[str] | None = None,
) -> list[str]:
    """Discover article links on a homepage, filtered by URL keywords."""
    logger.info("Discovering article links on: %s (max=%d)", homepage_url, max_links)
    session = session or _build_session()
    keywords = keywords or ["blog", "news", "article", "post", "press", "insight"]

    response = _get_with_retry(session, homepage_url)
    soup = BeautifulSoup(response.text, "html.parser")

    base_domain = urlparse(homepage_url).netloc
    seen: set[str] = set()
    links: list[str] = []

    for a_tag in soup.find_all("a", href=True):
        href: str = str(a_tag["href"]).strip()
        full_url = urljoin(homepage_url, href)
        parsed = urlparse(full_url)

        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc != base_domain:
            continue
        if full_url in seen:
            continue
        if not any(kw in full_url.lower() for kw in keywords):
            continue

        seen.add(full_url)
        links.append(full_url)
        if len(links) >= max_links:
            break

    logger.info("Found %d article links on %s", len(links), homepage_url)
    return links


def scrape_sites(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scrape multiple sites defined by a list of config dicts.

    Each dict accepts:
        homepage     (required) – URL to crawl for article links
        name         – human-readable site name
        max_articles – maximum articles to scrape per site (default: 5)
        keywords     – URL keyword filters for article discovery
    """
    session = _build_session()
    all_articles: list[dict[str, Any]] = []

    for site in sites:
        name = site.get("name", site.get("homepage", "Unknown"))
        logger.info("Processing site: %s", name)
        try:
            links = find_article_links(
                site["homepage"],
                session=session,
                max_links=site.get("max_articles", 5),
                keywords=site.get("keywords"),
            )
        except requests.RequestException as exc:
            logger.error("Failed to fetch links for %s: %s", name, exc)
            continue

        for link in links:
            try:
                article = scrape_article(link, session=session)
                article["source_name"] = name
                all_articles.append(article)
                time.sleep(config.request_delay)
            except requests.RequestException as exc:
                logger.warning("Failed to scrape %s: %s", link, exc)

    return all_articles


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    config.setup_logging()

    _sites = [
        {
            "name": "Microsoft 365 Blog",
            "homepage": "https://www.microsoft.com/en-us/microsoft-365/blog/",
            "max_articles": 3,
        },
        {
            "name": "Salesforce News",
            "homepage": "https://www.salesforce.com/news/",
            "max_articles": 3,
        },
    ]

    articles = scrape_sites(_sites)
    config.raw_data_dir.mkdir(parents=True, exist_ok=True)

    with config.articles_path.open("w", encoding="utf-8") as fh:
        json.dump(articles, fh, indent=2)

    logger.info("Saved %d articles to %s", len(articles), config.articles_path)
    for i, a in enumerate(articles, 1):
        logger.info("%d. %s (%d words)", i, a["title"][:70], a["word_count"])