import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Use the same local model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    """Get embedding for a piece of text using local model"""
    return model.encode(text)

def search(query, top_k=3):
    """Search for relevant chunks given a query"""
    print(f"Searching for: '{query}'")
    
    # Load FAISS index
    index = faiss.read_index("data/processed/faiss_index.bin")
    
    # Load chunk metadata
    with open("data/processed/chunks_metadata.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    # Get query embedding
    query_embedding = get_embedding(query)
    query_vector = np.array([query_embedding]).astype('float32')
    
    # Search
    distances, indices = index.search(query_vector, top_k)
    
    # Format results
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "chunk": chunks[idx],
            "distance": float(distances[0][i]),
            "rank": i + 1
        })
    
    return results

if __name__ == "__main__":
    # Example queries
    queries = [
        "What are Microsoft's latest product updates?",
        "What is Salesforce announcing?",
    ]
    
    for query in queries:
        print("\n" + "="*60)
        results = search(query, top_k=3)
        
        for result in results:
            print(f"\n--- Result {result['rank']} (distance: {result['distance']:.4f}) ---")
            print(f"Source: {result['chunk']['source']}")
            print(f"Text: {result['chunk']['text'][:300]}...")