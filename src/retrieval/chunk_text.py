"""Text chunking with sentence-boundary awareness.

Replaces fixed character-based splitting with sentence-accumulation logic:
  - sentences are added to the current chunk until *chunk_size* chars is reached
  - the tail of each chunk is carried forward as an overlap buffer

Run from project root:
    python -m src.retrieval.chunk_text
"""

import json
import logging
import os
import re
import sys
from typing import Any

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import config  # noqa: E402

logger = logging.getLogger(__name__)

_SENTENCE_ENDINGS = re.compile(r"(?<=[.!?])\s+")


# ── Sentence splitting ──────────────────────────────────────────────────────────

def _split_sentences(text: str) -> list[str]:
    """Split *text* into sentences using punctuation heuristics."""
    raw = _SENTENCE_ENDINGS.split(text)
    return [s.strip() for s in raw if s.strip()]


# ── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """Split *text* into overlapping chunks that respect sentence boundaries.

    Sentences are accumulated until *chunk_size* characters is reached, then
    the last N characters worth of sentences are carried forward as an overlap
    buffer before starting the next chunk.
    """
    chunk_size = chunk_size or config.chunk_size
    overlap = overlap or config.chunk_overlap

    if not text.strip():
        return []

    sentences = _split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        slen = len(sentence)
        if current_len + slen > chunk_size and current:
            chunk_str = " ".join(current).strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Build overlap from the tail of the current chunk
            overlap_buf: list[str] = []
            overlap_len = 0
            for s in reversed(current):
                if overlap_len + len(s) > overlap:
                    break
                overlap_buf.insert(0, s)
                overlap_len += len(s)
            current = overlap_buf
            current_len = overlap_len

        current.append(sentence)
        current_len += slen + 1  # +1 for joining space

    if current:
        final = " ".join(current).strip()
        if final:
            chunks.append(final)

    return chunks


def chunk_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn a list of article dicts into a flat list of enriched chunk dicts."""
    all_chunks: list[dict[str, Any]] = []
    for article in articles:
        content = article.get("content", "").strip()
        if not content:
            logger.warning("Empty content for: %s", article.get("url", "unknown"))
            continue

        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "source": article.get("url", ""),
                "source_name": article.get("source_name", ""),
                "title": article.get("title", ""),
                "scraped_at": article.get("scraped_at", ""),
                "chunk_id": i,
                "total_chunks": len(chunks),
                "text": chunk,
                "char_count": len(chunk),
            })

    return all_chunks


def main() -> None:
    config.setup_logging()
    logger.info("Loading articles from %s", config.articles_path)
    with config.articles_path.open("r", encoding="utf-8") as fh:
        articles: list[dict[str, Any]] = json.load(fh)

    all_chunks = chunk_articles(articles)
    config.processed_data_dir.mkdir(parents=True, exist_ok=True)

    with config.chunks_path.open("w", encoding="utf-8") as fh:
        json.dump(all_chunks, fh, indent=2)

    logger.info(
        "Created %d chunks from %d articles",
        len(all_chunks),
        len(articles),
    )


if __name__ == "__main__":
    main()
