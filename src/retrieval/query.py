"""Semantic search over the FAISS index.

Key improvements:
  - FAISS index and metadata are loaded once and cached (lru_cache)
  - Supports optional source_filter and max_distance threshold
  - Returns relevance_score (0–1) derived from L2 distance
  - invalidate_caches() lets callers force a reload after re-indexing

Run from project root:
    python -m src.retrieval.query
"""

from __future__ import annotations

import json
import logging
import os
import sys
from functools import lru_cache
from typing import Any

import faiss
import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import config  # noqa: E402
from src.retrieval.embed_and_index import get_model  # noqa: E402

logger = logging.getLogger(__name__)


# ── Cached assets ───────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def _load_index() -> faiss.Index:
    path = str(config.faiss_index_path)
    logger.info("Loading FAISS index from %s", path)
    return faiss.read_index(path)


@lru_cache(maxsize=1)
def _load_metadata() -> list[dict[str, Any]]:
    logger.info("Loading metadata from %s", config.chunks_metadata_path)
    with config.chunks_metadata_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def invalidate_caches() -> None:
    """Force reload of index and metadata on next search (call after re-indexing)."""
    _load_index.cache_clear()
    _load_metadata.cache_clear()
    logger.info("Search caches cleared.")


# ── Search ───────────────────────────────────────────────────────────────────


def search(
    query: str,
    top_k: int | None = None,
    *,
    source_filter: str | None = None,
    max_distance: float | None = None,
) -> list[dict[str, Any]]:
    """Embed *query* and return the top-k most relevant chunks.

    Args:
        query: Natural-language question.
        top_k: Number of results (default: ``config.default_top_k``).
        source_filter: Only return chunks whose source URL contains this string.
        max_distance: Drop chunks with L2 distance above this threshold.

    Returns:
        List of result dicts with keys: chunk, distance, relevance_score, rank.
    """
    if not query.strip():
        raise ValueError("Query must not be empty.")

    top_k = top_k or config.default_top_k
    max_distance = max_distance if max_distance is not None else config.distance_threshold

    logger.info("Searching: '%s' (top_k=%d)", query, top_k)

    index = _load_index()
    chunks = _load_metadata()

    model = get_model()
    query_vec = model.encode([query], convert_to_numpy=True).astype("float32")

    distances, indices = index.search(query_vec, top_k)

    results: list[dict[str, Any]] = []
    for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
        if idx == -1 or dist > max_distance:
            continue
        chunk = chunks[idx]
        if source_filter and source_filter.lower() not in chunk.get("source", "").lower():
            continue
        results.append({
            "chunk": chunk,
            "distance": float(dist),
            "relevance_score": round(1.0 / (1.0 + float(dist)), 4),
            "rank": rank,
        })

    logger.info("Found %d results for query: '%s'", len(results), query)
    return results


if __name__ == "__main__":
    config.setup_logging()

    sample_queries = [
        "What are Microsoft's latest product updates?",
        "What is Salesforce announcing?",
    ]
    for q in sample_queries:
        print(f"\n{'='*60}\n{q}")
        for r in search(q):
            print(f"  [{r['rank']}] score={r['relevance_score']} | {r['chunk']['source']}")
            print(f"       {r['chunk']['text'][:200]}…")