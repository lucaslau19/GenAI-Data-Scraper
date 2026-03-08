"""FastAPI backend for the GenAI Competitive Insights system.

Exposes REST endpoints consumed by the Next.js frontend.

Run from project root:
    uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import config  # noqa: E402
from src.ingest.news_scraper import scrape_sites  # noqa: E402
from src.llm.agent import answer_question  # noqa: E402
from src.retrieval.chunk_text import chunk_articles  # noqa: E402
from src.retrieval.embed_and_index import build_or_update_index  # noqa: E402
from src.retrieval.query import invalidate_caches, search  # noqa: E402

config.setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GenAI Competitive Insights API",
    description="RAG-powered competitive intelligence platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Embedding pipeline status ─────────────────────────────────────────────────

_embed_status: dict[str, Any] = {
    "status": "idle",
    "message": "",
    "progress": 0,
    "error": None,
}
_status_lock = threading.Lock()


def _set_status(status: str, message: str, progress: int, error: str | None = None) -> None:
    with _status_lock:
        _embed_status.update({"status": status, "message": message, "progress": progress, "error": error})


# ── Request / Response models ─────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    urls: list[str]
    max_articles_per_site: int = 5

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, urls: list[str]) -> list[str]:
        from urllib.parse import urlparse

        valid: list[str] = []
        for raw in urls:
            url = raw.strip()
            if not url:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url!r}")
            valid.append(url)
        if not valid:
            raise ValueError("At least one valid URL is required.")
        return valid


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    use_llm: bool = True
    source_filter: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/scrape")
def scrape_urls(req: ScrapeRequest) -> dict[str, Any]:
    """Scrape article or homepage URLs and save results to disk."""
    sites = [
        {"homepage": url, "max_articles": req.max_articles_per_site}
        for url in req.urls
    ]
    try:
        articles = scrape_sites(sites)
    except Exception as exc:
        logger.exception("Scraping failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    config.raw_data_dir.mkdir(parents=True, exist_ok=True)
    with config.articles_path.open("w", encoding="utf-8") as fh:
        json.dump(articles, fh, indent=2)

    failed = max(0, len(req.urls) - len({a["url"] for a in articles}))
    return {"scraped": len(articles), "failed": failed, "articles": articles}


@app.post("/api/embed")
def generate_embeddings(background_tasks: BackgroundTasks) -> dict[str, str]:
    """Chunk articles and rebuild embeddings (runs in background)."""

    def _run() -> None:
        try:
            _set_status("running", "Loading articles…", 10)
            with config.articles_path.open("r", encoding="utf-8") as fh:
                articles: list[dict[str, Any]] = json.load(fh)

            _set_status("running", f"Chunking {len(articles)} articles…", 30)
            chunks = chunk_articles(articles)
            config.processed_data_dir.mkdir(parents=True, exist_ok=True)
            with config.chunks_path.open("w", encoding="utf-8") as fh:
                json.dump(chunks, fh, indent=2)

            _set_status("running", f"Embedding {len(chunks)} chunks…", 55)
            build_or_update_index(chunks)
            invalidate_caches()

            _set_status("done", f"Indexed {len(chunks)} chunks from {len(articles)} articles.", 100)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Embedding pipeline failed")
            _set_status("error", str(exc), 0, error=str(exc))

    _set_status("running", "Starting embedding pipeline…", 5)
    background_tasks.add_task(_run)
    return {"status": "started", "message": "Embedding pipeline is running in the background."}


@app.get("/api/embed/status")
def get_embed_status() -> dict[str, Any]:
    """Poll this endpoint to track embedding progress."""
    with _status_lock:
        return dict(_embed_status)


@app.post("/api/query")
def query_index(req: QueryRequest) -> dict[str, Any]:
    """Answer a natural-language question against the indexed knowledge base."""
    if not req.query.strip():
        raise HTTPException(status_code=422, detail="Query must not be empty.")

    try:
        response = answer_question(
            req.query,
            top_k=req.top_k,
            use_llm=req.use_llm,
            source_filter=req.source_filter,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Index not found. Please scrape and embed articles first.",
        ) from exc
    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return response
