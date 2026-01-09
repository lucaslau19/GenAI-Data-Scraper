import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Use a free local model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    """Get embedding for a piece of text using local model"""
    return model.encode(text)

def main():
    print("Loading chunks...")
    with open("data/processed/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    print(f"Embedding {len(chunks)} chunks using local model...")
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        emb = get_embedding(chunk["text"])
        embeddings.append(emb)
        if (i + 1) % 10 == 0 or (i + 1) == len(chunks):
            print(f"  Processed {i + 1}/{len(chunks)}")
    
    print("Creating FAISS index...")
    embeddings_array = np.array(embeddings).astype('float32')
    
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    os.makedirs("data/processed", exist_ok=True)
    faiss.write_index(index, "data/processed/faiss_index.bin")
    
    with open("data/processed/chunks_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    
    print(f"✓ Created FAISS index with {len(chunks)} vectors")
    print(f"✓ Saved to data/processed/faiss_index.bin")
    print(f"✓ Model dimension: {dimension}")

if __name__ == "__main__":
    main()