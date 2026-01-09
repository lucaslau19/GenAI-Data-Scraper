import sys
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.retrieval.query import search
from src.llm.agent import answer_question

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test questions with expected topics
TEST_CASES = [
    {
        "question": "What products or features did Microsoft announce?",
        "expected_keywords": ["microsoft", "product", "feature"],
        "category": "Product Updates"
    },
    {
        "question": "What is Salesforce's latest news?",
        "expected_keywords": ["salesforce"],
        "category": "Company News"
    }
]

def evaluate_retrieval(question, top_k=5):
    """Evaluate retrieval quality"""
    results = search(question, top_k=top_k)
    
    # Calculate average distance (lower is better)
    avg_distance = sum(r['distance'] for r in results) / len(results)
    
    # Check if results are diverse (different sources)
    unique_sources = len(set(r['chunk']['source'] for r in results))
    
    return {
        "avg_distance": avg_distance,
        "unique_sources": unique_sources,
        "total_results": len(results)
    }

def evaluate_answer_quality(question, answer, expected_keywords):
    """Evaluate answer quality using LLM as a judge"""
    
    eval_prompt = f"""Evaluate the quality of this answer on a scale of 1-5:

Question: {question}
Answer: {answer}

Rate the answer based on:
1. Relevance to the question
2. Completeness 
3. Accuracy (based on what you can assess)
4. Clarity

Provide your rating as a single number from 1-5, followed by a brief explanation.
Format: RATING: X
EXPLANATION: ..."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an objective evaluator of AI-generated answers."},
            {"role": "user", "content": eval_prompt}
        ],
        temperature=0
    )
    
    eval_text = response.choices[0].message.content
    
    # Parse rating
    try:
        rating_line = [line for line in eval_text.split('\n') if 'RATING:' in line][0]
        rating = int(rating_line.split(':')[1].strip())
    except:
        rating = 0
    
    # Check keyword presence
    answer_lower = answer.lower()
    keywords_found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    keyword_coverage = keywords_found / len(expected_keywords) if expected_keywords else 0
    
    return {
        "llm_rating": rating,
        "keyword_coverage": keyword_coverage,
        "evaluation_text": eval_text
    }

def run_evaluation():
    """Run full evaluation suite"""
    print("="*80)
    print("COMPETITIVE INSIGHTS RAG SYSTEM EVALUATION")
    print("="*80)
    
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n\nTest Case {i}/{len(TEST_CASES)}: {test_case['category']}")
        print("-"*80)
        print(f"Question: {test_case['question']}")
        
        # Evaluate retrieval
        retrieval_metrics = evaluate_retrieval(test_case['question'])
        print(f"\nRetrieval Metrics:")
        print(f"  Average Distance: {retrieval_metrics['avg_distance']:.4f}")
        print(f"  Unique Sources: {retrieval_metrics['unique_sources']}")
        
        # Generate answer
        answer, sources = answer_question(test_case['question'], top_k=3)
        
        # Evaluate answer
        answer_metrics = evaluate_answer_quality(
            test_case['question'], 
            answer, 
            test_case['expected_keywords']
        )
        
        print(f"\nAnswer Quality:")
        print(f"  LLM Rating: {answer_metrics['llm_rating']}/5")
        print(f"  Keyword Coverage: {answer_metrics['keyword_coverage']:.2%}")
        
        print(f"\nGenerated Answer:")
        print(answer)
        
        results.append({
            "test_case": test_case,
            "retrieval_metrics": retrieval_metrics,
            "answer_metrics": answer_metrics,
            "answer": answer
        })
    
    # Overall summary
    print("\n\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    
    avg_rating = sum(r['answer_metrics']['llm_rating'] for r in results) / len(results)
    avg_coverage = sum(r['answer_metrics']['keyword_coverage'] for r in results) / len(results)
    
    print(f"Average Answer Quality: {avg_rating:.2f}/5")
    print(f"Average Keyword Coverage: {avg_coverage:.2%}")
    
    # Save results
    os.makedirs("data/evaluation", exist_ok=True)
    with open("data/evaluation/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to data/evaluation/results.json")
    
    return results

if __name__ == "__main__":
    run_evaluation()