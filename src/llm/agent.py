"""RAG agent: retrieves relevant chunks and synthesizes an answer.

Behaviour:
  - If OPENAI_API_KEY is set and use_llm=True, calls GPT to generate a cited answer.
  - Otherwise, falls back to a structured retrieval-only answer (no API required).

Run from project root:
    python -m src.llm.agent
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.config import config  # noqa: E402
from src.retrieval.query import search  # noqa: E402

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """\
You are a competitive intelligence analyst. Answer questions about competitor news and product
developments using ONLY the provided source excerpts below.

Rules:
- Cite sources by referencing the [Source N] labels in your answer.
- If the context does not contain enough information, say so explicitly.
- Be concise and direct. Avoid speculation.
"""

_USER_TEMPLATE = """\
Context excerpts (most relevant first):

{context}

---

Question: {question}

Answer (cite sources using [Source N]):"""


# ── Context builder ──────────────────────────────────────────────────────────


def _build_context(results: list[dict[str, Any]]) -> str:
    parts = []
    for r in results:
        chunk = r["chunk"]
        parts.append(
            f"[Source {r['rank']}] {chunk.get('title', 'Unknown Title')}\n"
            f"URL: {chunk['source']}\n"
            f"{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)


# ── LLM call ──────────────────────────────────────────────────────────────────


def _llm_answer(question: str, context: str) -> str:
    """Call the OpenAI Chat API to generate a grounded answer."""
    try:
        from openai import OpenAI  # local import: avoid hard dep if key absent
    except ImportError as exc:
        raise RuntimeError(
            "openai package is not installed. Run: pip install openai"
        ) from exc

    if not config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

    client = OpenAI(api_key=config.openai_api_key)
    response = client.chat.completions.create(
        model=config.openai_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _USER_TEMPLATE.format(context=context, question=question),
            },
        ],
        temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens,
    )
    return response.choices[0].message.content.strip()


def _fallback_answer(results: list[dict[str, Any]]) -> str:
    """Build a structured answer directly from retrieved chunks (no LLM)."""
    lines = ["Based on the retrieved information:\n"]
    for r in results:
        chunk = r["chunk"]
        snippet = chunk["text"][:300].rstrip()
        lines.append(
            f"[Source {r['rank']}] {chunk.get('title', '')} ({chunk['source']})\n{snippet}…\n"
        )
    lines.append(
        "\nNote: Set OPENAI_API_KEY in your .env file for an LLM-synthesized answer."
    )
    return "\n".join(lines)


# ── Public API ─────────────────────────────────────────────────────────────────


def answer_question(
    question: str,
    top_k: int | None = None,
    *,
    use_llm: bool = True,
    source_filter: str | None = None,
) -> dict[str, Any]:
    """Answer *question* using retrieval + optional LLM synthesis.

    Returns a dict with:
        answer       – str: LLM response or structured retrieval fallback
        results      – list: retrieved chunks with scores
        used_llm     – bool: whether an LLM was used
        sources      – list[str]: unique source URLs
    """
    logger.info("Answering: '%s'", question)
    results = search(question, top_k=top_k, source_filter=source_filter)

    if not results:
        return {
            "answer": "No relevant information found in the knowledge base.",
            "results": [],
            "used_llm": False,
            "sources": [],
        }

    context = _build_context(results)
    used_llm = False
    answer: str

    if use_llm and config.openai_api_key:
        try:
            answer = _llm_answer(question, context)
            used_llm = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM call failed (%s). Falling back to retrieval-only.", exc)
            answer = _fallback_answer(results)
    else:
        answer = _fallback_answer(results)

    sources = list(dict.fromkeys(r["chunk"]["source"] for r in results))
    return {
        "answer": answer,
        "results": results,
        "used_llm": used_llm,
        "sources": sources,
    }


if __name__ == "__main__":
    config.setup_logging()
    response = answer_question("What new features or products has Microsoft announced?")
    print("\n" + "=" * 80)
    print("ANSWER:")
    print("=" * 80)
    print(response["answer"])
    print(f"\nSources: {response['sources']}")
    print(f"Used LLM: {response['used_llm']}")