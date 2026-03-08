# GenAI Competitive Insights

AI-powered competitive intelligence: scrape competitor sites → semantic search → LLM-synthesized answers.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Browser (Next.js 14)                        │
│  Home → URL input → /analyze → ProcessingStatus + QueryUI      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST (localhost:3000/api/*)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Next.js API Routes  (port 3000)                    │
│  /api/scrape  /api/embed  /api/embed/status  /api/query         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP → localhost:8000
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend  (port 8000)                       │
│  scraper → chunker → embedder (FAISS) → query → LLM agent      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+  
- Node.js 18+  
- (Optional) OpenAI API key for LLM-synthesized answers

### 1. Python backend

```bash
# From project root
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -e .
pip install -r requirements.txt
```

Copy the env template:

```bash
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux
```

`.env` contents:
```
OPENAI_API_KEY=sk-...    # optional — retrieval works without it
LOG_LEVEL=INFO
```

Start FastAPI:

```bash
uvicorn src.api.main:app --reload --port 8000
```

Interactive API docs: http://localhost:8000/docs

### 2. Next.js frontend

```bash
cd web
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000

---

## CLI Usage

Run each pipeline step manually from the project root:

```bash
python -m src.ingest.news_scraper       # 1. Scrape articles
python -m src.retrieval.chunk_text      # 2. Chunk text
python -m src.retrieval.embed_and_index # 3. Build embeddings + FAISS
python -m src.retrieval.query           # 4. Interactive search
python -m src.llm.agent                 # 5. LLM answer
python -m src.evaluation.evaluate       # 6. Evaluate RAG quality
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/scrape` | Scrape URLs and save articles |
| POST | `/api/embed` | Chunk + embed articles (background) |
| GET | `/api/embed/status` | Poll embedding progress |
| POST | `/api/query` | Semantic search + optional LLM answer |

### POST `/api/scrape`
```json
{ "urls": ["https://example.com/blog/"], "max_articles_per_site": 5 }
```

### POST `/api/query`
```json
{ "query": "What products did Microsoft announce?", "top_k": 5, "use_llm": true }
```

---

## Configuration

All settings override via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | Optional LLM key |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embedding model |
| `CHUNK_SIZE` | `500` | Max chars per chunk |
| `CHUNK_OVERLAP` | `100` | Overlap chars between chunks |
| `DEFAULT_TOP_K` | `5` | Default search results |
| `DISTANCE_THRESHOLD` | `2.0` | Max L2 distance cutoff |
| `REQUEST_DELAY` | `1.0` | Seconds between scrape requests |
| `MAX_RETRIES` | `3` | HTTP retry attempts |
| `API_PORT` | `8000` | FastAPI port |

---

## Production Deployment

### Backend → Render / Railway / AWS ECS

```bash
pip install gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Update the `allow_origins` list in `src/api/main.py` with your frontend domain.

### Frontend → Vercel

```bash
cd web && npm run build
# or push to GitHub and connect Vercel
```

Set `PYTHON_API_URL` in Vercel environment variables to your backend URL.

### Scaling roadmap

| Concern | Now | Production upgrade |
|---|---|---|
| Vector DB | FAISS (local file) | Pinecone / Weaviate / pgvector |
| Storage | JSON files | PostgreSQL + Prisma |
| Background jobs | FastAPI BackgroundTasks | Celery + Redis |
| Query caching | None | Redis |
| Concurrency | Single process | Gunicorn multi-worker |

---

## Project Structure

```
genai-competitive-insights/
├── src/
│   ├── config.py               # Centralized settings (env-overridable)
│   ├── ingest/news_scraper.py  # Retry-safe scraper with structured logging
│   ├── retrieval/
│   │   ├── chunk_text.py       # Sentence-boundary-aware chunking
│   │   ├── embed_and_index.py  # Batch embedding + incremental FAISS updates
│   │   └── query.py            # Cached semantic search
│   ├── llm/agent.py            # RAG agent (LLM + retrieval-only fallback)
│   ├── evaluation/evaluate.py  # RAG evaluation suite
│   └── api/main.py             # FastAPI REST server
├── web/                        # Next.js 14 + Tailwind CSS frontend
│   ├── app/
│   │   ├── page.tsx            # Home / URL input page
│   │   ├── analyze/page.tsx    # Processing status + query interface
│   │   └── api/                # Next.js route handlers (proxy to FastAPI)
│   ├── components/             # ThemeToggle, ProcessingStatus, QueryInterface,
│   │                           # ResultCard, AnswerDisplay
│   └── lib/                    # API client (api.ts) + TypeScript types
├── data/
│   ├── raw/articles.json
│   └── processed/              # chunks.json, chunks_metadata.json, faiss_index.bin
├── requirements.txt
├── pyproject.toml
└── README.md
```

