import json
import os
from typing import List

RAW_DATA_PATH = "data/raw/articles.json"
OUTPUT_PATH = "data/processed/chunks.json"

CHUNK_SIZE = 500   # characters
CHUNK_OVERLAP = 100


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def main():
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    all_chunks = []

    for article in articles:
        content = article.get("content", "")
        url = article.get("url", "")

        chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "source": url,
                "chunk_id": i,
                "text": chunk
            })

    os.makedirs("data/processed", exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"Created {len(all_chunks)} chunks")


if __name__ == "__main__":
    main()
