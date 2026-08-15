# Architecture Decision Records — GitNova v4.2

> Lightweight ADRs documenting every major technology choice.
> Each record answers: Problem → Decision → Alternatives → Trade-offs → Consequences.

---

## ADR 0001 — Why FastAPI

**Status:** Accepted

### Problem
GitNova needs an HTTP API layer to serve pre-computed repository scores and AI mentor hints to the frontend.

### Decision
**FastAPI** + **Uvicorn** (ASGI server).

### Alternatives Considered
| Alternative | Reason Rejected |
|---|---|
| Flask | No native async. Slower under concurrent load. |
| Django | Too heavy for a simple read API. ORM adds complexity. |
| Fastify (Node) | Wrong ecosystem — entire pipeline is Python. |

### Trade-offs
✅ Async-native — handles concurrent DB reads efficiently
✅ Auto-generates OpenAPI docs at `/docs` — free documentation
✅ Pydantic v2 — type safety at the API boundary
✅ Industry standard for Python ML services — high interview value
⚠️ Slightly more boilerplate than Flask for simple endpoints

### Consequences
- All endpoints are `async`
- Request/response models are Pydantic `BaseModel` classes
- The API **never** calls an LLM — reads pre-computed data from Supabase only

---

## ADR 0002 — Why Supabase

**Status:** Accepted

### Problem
GitNova needs a hosted PostgreSQL database that supports pgvector for hybrid search, is free-tier compatible, and requires zero DevOps to manage.

### Decision
**Supabase** (hosted PostgreSQL + pgvector).

### Alternatives Considered
| Alternative | Reason Rejected |
|---|---|
| Neon | pgvector support is newer, less battle-tested |
| PlanetScale | MySQL — no pgvector support |
| Self-hosted PostgreSQL | Requires server management — too much DevOps for one dev |
| Pinecone | Dedicated vector DB — overkill, adds cost and complexity |

### Trade-offs
✅ Free: 500MB DB, 5GB egress/month
✅ pgvector built-in — no separate vector DB needed
✅ REST API + JS client — easy to query from GitHub Actions workers
⚠️ Auto-pauses after 7 days inactivity → mitigated by `keepalive.yml` workflow
⚠️ 500MB fills up — monitor aggressively, prune stale chunks

### Consequences
- `keepalive.yml` GitHub Actions workflow pings Supabase every 3 days
- All pipeline workers connect via `DATABASE_URL` environment variable
- FastAPI connects to Supabase via `asyncpg` connection pool

---

## ADR 0003 — Why pgvector

**Status:** Accepted

### Problem
GitNova needs to store code embeddings (768-dim vectors) and perform semantic search + full-text search in a single query for the RAG pipeline.

### Decision
**pgvector** extension on PostgreSQL with HNSW index and RRF (Reciprocal Rank Fusion) for hybrid search.

### Alternatives Considered
| Alternative | Reason Rejected |
|---|---|
| Pinecone | Separate service, adds cost and network hop |
| Weaviate | Separate service, overkill for V1 scale |
| Chroma | Local-only, not suitable for GitHub Actions workers |
| Pure FTS | Misses semantic similarity — can't find "fix the cookie bug" → session.py |

### Trade-offs
✅ One database for both relational data and vectors — simpler architecture
✅ HNSW index gives O(log n) approximate nearest-neighbor queries
✅ RRF combines semantic + lexical search without hyperparameter tuning
✅ No extra cost — runs inside Supabase free tier
⚠️ pgvector is slower than dedicated vector DBs at very high scale (10M+ vectors)

### Consequences
- Two SQL functions: `match_chunks_vector` and `match_chunks_fts`
- RRF fusion merges results in Python after fetching both result sets
- HNSW index created with `vector_cosine_ops` for cosine similarity

---

## ADR 0004 — Why LiteLLM

**Status:** Accepted

### Problem
GitNova uses two LLM providers (Groq primary, OpenRouter fallback). Without an abstraction layer, switching providers requires rewriting prompt code.

### Decision
**LiteLLM** as a single unified interface to all LLM providers.

### Alternatives Considered
| Alternative | Reason Rejected |
|---|---|
| Direct Groq SDK | Tight coupling — switching providers requires code changes |
| Direct OpenAI SDK | Same problem. Also not free-tier |
| LangChain | Massive dependency, complex abstractions, overkill for our use case |
| Manual if/else routing | Works but fragile and hard to maintain |

### Trade-offs
✅ One function call works with any provider — `litellm.completion(model="groq/...")`
✅ Built-in retry and fallback logic
✅ Easy to add new providers (NVIDIA NIM, Anthropic) later with zero code changes
⚠️ Adds one dependency layer — but LiteLLM is lightweight and widely used

### Consequences
- Provider cascade: Groq (primary) → OpenRouter (fallback)
- All LLM calls go through `backend/app/clients/llm.py`
- Switching providers in production = change one environment variable
