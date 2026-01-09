GenAI Competitive Insights Agent
A Retrieval-Augmented Generation (RAG) system that scrapes competitive intelligence from news sources and enables natural language queries about competitor activities.
Features

Web Scraping: Automated scraping of competitor news and blog posts
Text Processing: Chunking and preprocessing of scraped content
Vector Search: FAISS-based semantic search using sentence transformers
RAG Pipeline: Retrieval-augmented generation for answering competitive intelligence questions
Evaluation Framework: Automated evaluation of retrieval quality and answer accuracy

Tech Stack

Python 3.11
RAG Components:

Embeddings: sentence-transformers (all-MiniLM-L6-v2)
Vector DB: FAISS
LLM: OpenAI GPT-4o-mini (optional)


Web Scraping: BeautifulSoup4, requests
Data Processing: pandas, numpy

Project Structure
genai-competitive-insights/
│
├── data/
│   ├── raw/              # Scraped articles
│   └── processed/        # Chunked text and embeddings
│
├── src/
│   ├── ingest/           # Web scraping modules
│   ├── retrieval/        # Embedding and search
│   ├── llm/              # LLM integration
│   └── evaluation/       # Performance evaluation
│
├── requirements.txt
└── README.md

Setup

Clone the repository

bashgit clone https://github.com/yourusername/genai-competitive-insights.git
cd genai-competitive-insights

Create virtual environment

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bashpip install -r requirements.txt

Set up environment variables (optional, for LLM features)

bash# Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
Usage
1. Scrape Competitor Data
bashpython src/ingest/news_scraper.py
2. Process and Chunk Text
bashpython src/retrieval/chunk_text.py
3. Create Embeddings and Index
bashpython src/retrieval/embed_and_index.py
4. Query the System
bashpython src/retrieval/query.py
5. Run Full Agent (with LLM)
bashpython src/llm/agent.py
6. Evaluate Performance
bashpython src/evaluation/evaluate.py

Key Components
Web Scraper (src/ingest/news_scraper.py)

Scrapes competitor blogs and news sites
Extracts article content and metadata
Handles rate limiting and error recovery

Embedding & Indexing (src/retrieval/embed_and_index.py)

Converts text chunks to embeddings using sentence-transformers
Creates FAISS index for fast similarity search
Stores metadata for source attribution

Query System (src/retrieval/query.py)

Semantic search across scraped content
Returns top-k most relevant chunks
Supports flexible querying

RAG Agent (src/llm/agent.py)

Combines retrieval with LLM generation
Provides context-aware answers
Cites sources for transparency

Performance

Embedding Model: all-MiniLM-L6-v2 (384 dimensions)
Retrieval Speed: ~50ms per query
Index Size: Scales linearly with content volume
