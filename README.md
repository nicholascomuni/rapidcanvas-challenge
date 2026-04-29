# Bluesky Post Explainer

An AI agent that explains Bluesky posts by searching for relevant context and synthesizing 3-5 cited bullet points.

## Architecture

```
User URL
  → FastAPI backend
      1. Fetch post (Bluesky AT Protocol public API — no auth required)
      2. Generate search queries (GPT-4o-mini)
      3. Search the web in parallel (Tavily advanced search)
      4. Rerank results by semantic similarity (text-embedding-3-small) ← ML module
      5. Synthesize explanation with citations + optional image understanding (GPT-4o)
  → React frontend
      PostPreview + ExplanationCard (bullet points with citation chips) + SearchResultsPanel
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Tavily API key](https://app.tavily.com/) (1,000 free searches/month)

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url>
cd bluesky-explainer
cp .env.example backend/.env
# Edit backend/.env and fill in OPENAI_API_KEY and TAVILY_API_KEY
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) and paste any Bluesky post URL.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT-4o and embeddings |
| `TAVILY_API_KEY` | Yes | Tavily web search API key |
| `ALLOWED_ORIGINS` | No | JSON array of allowed CORS origins (default: localhost dev ports) |

## Running the Evaluation Harness

The harness tests 12 posts across diverse categories and scores each explanation on:
- **Coverage** — fraction of expected topics mentioned
- **Citation rate** — fraction of bullets with source citations
- **Hallucination** — checks for known-false claims
- **LLM judge** — GPT-4o-mini rates accuracy, relevance, clarity, context (1-5 each)

```bash
# With the backend running:
cd backend
python -m tests.eval.eval_runner

# Or via pytest:
pytest tests/eval/test_eval.py -v

# Unit tests (no API keys needed):
pytest tests/unit/ -v
```

Results are written to `backend/tests/eval/eval_report.json`.

## API

### `POST /api/v1/explain`

**Request:**
```json
{ "url": "https://bsky.app/profile/user.bsky.social/post/abc123" }
```

**Response:**
```json
{
  "post": {
    "author_handle": "user.bsky.social",
    "author_display_name": "User Name",
    "text": "Post text...",
    "image_urls": [],
    "created_at": "2025-01-05T22:56:00Z"
  },
  "bullets": [
    {
      "text": "The Ralph Wiggum technique is a bash loop pattern... [Source 1]",
      "citations": [{ "index": 1, "url": "https://...", "title": "..." }]
    }
  ],
  "search_results": [
    { "url": "https://...", "title": "...", "content": "...", "score": 0.82 }
  ],
  "reranking_scores": [0.82, 0.71, 0.65]
}
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Design Decisions

### Why Tavily over OpenAI's built-in web search?

OpenAI's Responses API has a `web_search` tool that folds retrieval into the generation step. It was rejected because:
- It makes the search step a black box — you can't inspect, test, or rerank the intermediate results
- Citations become opaque JSON annotations rather than structured objects you can render as UI chips
- The ML reranking module (a key differentiator) requires explicit access to retrieved documents

Tavily returns structured results with full raw content per query in a single call. The `search_depth="advanced"` mode scrapes pages deeply, and results can be embedded and reranked independently.

### Why a simple chain, not an agent loop?

The task is precisely defined: one URL in, one explanation out. An agent loop (ReAct-style, where the model decides whether to search again) adds unpredictable latency, harder testability, and no quality improvement for this use case. The intelligence lives in the reranker and the synthesizer prompt, not in iterative tool-calling.

### ML module: semantic reranking with text-embedding-3-small

After Tavily returns 10–15 results across 2-3 queries, a single batched embedding call computes cosine similarity between the post text and each result's raw content. The top 3 semantically closest results are passed to GPT-4o.

- **Why not BM25?** Keyword overlap misses thematically related content. A post saying "Ralph Wiggum technique" shares no keywords with an article about "agentic coding loops", but they're semantically close.
- **Cost:** ~$0.00002 per request (one batch call).
- **Transparency:** Reranking scores are returned in the API response and displayed as percentage bars in the UI.

### `response_format=json_object` on the synthesizer

Guarantees structured output without prompt fragility. Parsing is a single `json.loads()` + Pydantic `model_validate()` call. No regex, no "GPT added markdown fences" bugs.

### Image understanding (bonus)

When the Bluesky post contains an image, its CDN thumbnail URL is passed to GPT-4o as a vision message (`detail: "low"` to minimize token cost). The synthesizer prompt instructs the model to incorporate visual context into the bullets.

## Bonus Features Implemented

- **Image understanding** — vision message passed to GPT-4o for posts with images
- **Source citations** — each bullet has citation chips linking to the source URL
- **Semantic reranking (ML module)** — text-embedding-3-small cosine similarity filtering

## Known Limitations

- **Private accounts** — the AT Protocol public API only works for public posts
- **Rate limits** — Bluesky's public XRPC API has undocumented rate limits; the service retries 3× with exponential backoff
- **Deleted posts** — will return a 404 error from the Bluesky API
- **Very short/ambiguous posts** — search query generation may produce broad queries; results may be less targeted
- **Tavily free tier** — 1,000 searches/month; each explain request uses 2-3 searches
