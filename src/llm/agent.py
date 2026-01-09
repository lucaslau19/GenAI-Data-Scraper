import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.retrieval.query import search

def answer_question(question, top_k=3):
    """Answer a question using retrieval (without LLM for now)"""
    
    print(f"\nQuestion: {question}")
    print("-" * 60)
    
    # Retrieve relevant chunks
    print("Retrieving relevant information...")
    results = search(question, top_k=top_k)
    
    # Format answer from retrieved chunks
    print("\nRetrieved Context:")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        source = result['chunk']['source']
        text = result['chunk']['text']
        distance = result['distance']
        
        print(f"\n[Result {i}] (Relevance: {1/(1+distance):.2f})")
        print(f"Source: {source}")
        print(f"Content: {text}")
        print("-" * 60)
    
    # Simple answer synthesis (rule-based, no LLM needed)
    answer = f"""Based on the retrieved information:

The most relevant content comes from {results[0]['chunk']['source']}.

Key information found:
"""
    
    for i, result in enumerate(results, 1):
        snippet = result['chunk']['text'][:200]
        answer += f"\n{i}. {snippet}..."
    
    answer += "\n\nNote: This is a retrieval-based answer. For better analysis, you would need an LLM API (OpenAI, Anthropic, or local model like Ollama)."
    
    return answer, results

if __name__ == "__main__":
    # Example questions
    questions = [
        "What new features or products has Microsoft announced?",
        "What is Salesforce's latest news?",
    ]
    
    for question in questions:
        print("\n" + "="*80)
        answer, sources = answer_question(question, top_k=3)
        
        print("\n" + "="*80)
        print("ANSWER:")
        print("="*80)
        print(answer)