"""Embedding generation and FAISS index management.

Key improvements over the original:
  - Singleton model via functools.lru_cache (avoid reloading across calls)
  - Batch encoding via SentenceTransformer's built-in batching
  - Incremental updates: only embed chunks from sources not yet indexed
  - force_rebuild flag to wipe and rebuild from scratch

Run from project root:
    python -m src.retrieval.embed_and_index
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
from sentence_transformers import SentenceTransformer

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import config  # noqa: E402

logger = logging.getLogger(__name__)


# ── Singleton model ─────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load (and cache) the embedding model."""
    logger.info("Loading embedding model: %s", config.embedding_model)
    return SentenceTransformer(config.embedding_model)


# ── Embedding helpers ───────────────────────────────────────────────────────────


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed *texts* using the cached model with automatic batching."""
    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=config.embedding_batch_size,
        show_progress_bar=len(texts) > 50,
        convert_to_numpy=True,
    )
    return embeddings.astype("float32")  # type: ignore[return-value]


# ── FAISS index management ────────────────────────────────────────────────────────


def _load_existing() -> tuple[list[dict[str, Any]], set[str]]:
    """Return existing metadata and the set of already-indexed source URLs."""
    if not config.chunks_metadata_path.exists():
        return [], set()
    with config.chunks_metadata_path.open("r", encoding="utf-8") as fh:
        existing: list[dict[str, Any]] = json.load(fh)
    known = {item["source"] for item in existing}
    return existing, known


def build_or_update_index(
    chunks: list[dict[str, Any]],
    *,
    force_rebuild: bool = False,
) -> faiss.Index:
    """Build a new or update the existing FAISS index.

    If *force_rebuild* is True, the existing index is discarded. Otherwise,
    only chunks from previously unseen source URLs are appended.
    """
    existing, known = ([], set()) if force_rebuild else _load_existing()
    new_chunks = [c for c in chunks if c["source"] not in known]

    if not new_chunks:
        logger.info("No new chunks to index — loading existing index.")
        return faiss.read_index(str(config.faiss_index_path))

    logger.info(
        "Embedding %d new chunks (skipping %d already indexed)…",
        len(new_chunks),
        len(existing),
    )
    texts = [c["text"] for c in new_chunks]
    new_embeddings = embed_texts(texts)

    if config.faiss_index_path.exists() and not force_rebuild:
        logger.info("Appending to existing FAISS index…")
        index = faiss.read_index(str(config.faiss_index_path))
    else:
        dimension = new_embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        logger.info("Created new FAISS IndexFlatL2 (dim=%d)", dimension)

    index.add(new_embeddings)
    all_chunks = existing + new_chunks

    config.processed_data_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(config.faiss_index_path))
    with config.chunks_metadata_path.open("w", encoding="utf-8") as fh:
        json.dump(all_chunks, fh, indent=2)

    logger.info(
        "Index updated: %d total vectors (+%d new), saved to %s",
        index.ntotal,
        len(new_chunks),
        config.faiss_index_path,
    )
    return index


def main() -> None:
    config.setup_logging()
    logger.info("Loading chunks from %s", config.chunks_path)
    with config.chunks_path.open("r", encoding="utf-8") as fh:
        chunks: list[dict[str, Any]] = json.load(fh)
    build_or_update_index(chunks)


if __name__ == "__main__":
    main()