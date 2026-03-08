"""Centralized configuration management.

All tuneable values live here and can be overridden via environment variables.
Copy .env.example to .env and add your API keys before running.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass
class Config:
    # ── Paths ──────────────────────────────────────────────────────────────
    raw_data_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "raw")
    processed_data_dir: Path = field(default_factory=lambda: BASE_DIR / "data" / "processed")

    @property
    def articles_path(self) -> Path:
        return self.raw_data_dir / "articles.json"

    @property
    def chunks_path(self) -> Path:
        return self.processed_data_dir / "chunks.json"

    @property
    def chunks_metadata_path(self) -> Path:
        return self.processed_data_dir / "chunks_metadata.json"

    @property
    def faiss_index_path(self) -> Path:
        return self.processed_data_dir / "faiss_index.bin"

    # ── HTTP / scraper ─────────────────────────────────────────────────────
    request_timeout: int = int(_env("REQUEST_TIMEOUT", "15"))
    request_delay: float = float(_env("REQUEST_DELAY", "1.0"))
    max_retries: int = int(_env("MAX_RETRIES", "3"))
    user_agent: str = _env(
        "USER_AGENT",
        "Mozilla/5.0 (compatible; CompetitiveInsightsBot/1.0)",
    )

    # ── Chunking ───────────────────────────────────────────────────────────
    chunk_size: int = int(_env("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(_env("CHUNK_OVERLAP", "100"))

    # ── Embedding ──────────────────────────────────────────────────────────
    embedding_model: str = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_batch_size: int = int(_env("EMBEDDING_BATCH_SIZE", "64"))

    # ── Search ─────────────────────────────────────────────────────────────
    default_top_k: int = int(_env("DEFAULT_TOP_K", "5"))
    distance_threshold: float = float(_env("DISTANCE_THRESHOLD", "2.0"))

    # ── LLM ────────────────────────────────────────────────────────────────
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_model: str = _env("OPENAI_MODEL", "gpt-4o-mini")
    llm_temperature: float = float(_env("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(_env("LLM_MAX_TOKENS", "1024"))

    # ── API server ─────────────────────────────────────────────────────────
    api_host: str = _env("API_HOST", "0.0.0.0")
    api_port: int = int(_env("API_PORT", "8000"))

    # ── Logging ────────────────────────────────────────────────────────────
    log_level: str = _env("LOG_LEVEL", "INFO")

    def setup_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


config = Config()
