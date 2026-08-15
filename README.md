# GitNova v4.2 🚀

> **Find your first successful open-source contribution with confidence.**

GitNova is an AI Open Source Mentor. It doesn't just show you a list of issues and say "good luck." It first scores every repository on contributor-friendliness, then retrieves actual source code, grounds an LLM in that code, and generates a step-by-step fix blueprint.

[![CI](https://github.com/sriharizz/gitnova/actions/workflows/ci.yml/badge.svg)](https://github.com/sriharizz/gitnova/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-4.2.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20Supabase%20%2B%20Groq-purple)

---

## What GitNova Does

| Question | How GitNova Answers |
|---|---|
| Which repos are worth contributing to? | Repository Qualification Engine → **Contribution Success Score** |
| Which issue should I choose? | Issue Intelligence + DeBERTa classification |
| Why is it suitable for me? | Competition scoring + difficulty estimation |
| What code should I read? | Hybrid RAG (vector + full-text search) |
| How should I approach it? | LLM Mentor with file-level guidance |

---

## Architecture

```
GitHub Actions (Workers)          FastAPI (Render)
──────────────────────            ────────────────
Weekly:                           Always on:
  GitHub Search API               GET /repos?tier=starter
  → Score repos (0-100)           GET /repos/{id}
  → Store in Supabase             GET /issues?quality=high
                                  GET /issues/{id}
Every 12h:                        GET /health
  Scan issues
  → Classify (DeBERTa)                 ↓
  → RAG retrieve code             Supabase (PostgreSQL + pgvector)
  → LLM hint (Groq)
  → Validate + publish
```

**Key insight:** The API never calls an LLM. It reads pre-computed data. This is why it's fast, cheap, and stays alive on free tiers.

---

## Quick Start

### Prerequisites
- Docker + Docker Compose
- A [Supabase](https://supabase.com) project (free)
- A [Groq](https://console.groq.com) API key (free)
- A GitHub personal access token

### 1. Clone
```bash
git clone https://github.com/sriharizz/gitnova.git
cd gitnova
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your Supabase URL, Groq key, and GitHub token
```

### 3. Run
```bash
docker compose up --build
```

API is live at: `http://localhost:8000`
Docs at: `http://localhost:8000/docs`

### Optional: Local DB (no Supabase)
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| **API** | FastAPI + Uvicorn | Async, auto-docs, industry standard |
| **Database** | Supabase (PostgreSQL + pgvector) | Free hosted, vector search built-in |
| **LLM** | Groq (primary) → OpenRouter (fallback) via LiteLLM | Free tier, reliable cascade |
| **Embeddings** | Jina v2 (local CPU) | No API cost, no rate limits |
| **Classifier** | DeBERTa v3 (zero-shot) | Strong NLI, no fine-tuning needed |
| **Orchestration** | GitHub Actions | Free for public repos, unlimited minutes |
| **Deployment** | Render (API) + GitHub Pages (frontend) | Free tier |

---

## Contribution Success Score

GitNova scores every repository across 5 pillars:

| Pillar | Weight | What It Measures |
|---|---|---|
| **Beginner-Friendliness** | 25% | CONTRIBUTING.md, good-first-issue labels |
| **Responsiveness** | 20% | PR merge rate, merge time, issue response |
| **Activity** | 20% | Recent commits, issue velocity |
| **Health** | 20% | License, community size, manageable backlog |
| **Documentation** | 15% | README quality, Code of Conduct |

Repos with score ≥ 60 enter the `starter` tier. Score ≥ 50 → `growing`. Score ≥ 40 → `established`.

---

## Project Structure

```
gitnova/
├── backend/app/
│   ├── main.py              ← FastAPI entry point
│   ├── intelligence/        ← Repository Qualification Engine (Sprint 3)
│   ├── pipeline/            ← Issue scanning + RAG + LLM (Sprints 5-9)
│   ├── indexer/             ← Code chunking + embeddings (Sprint 5)
│   └── db/                  ← Database client (Sprint 1)
├── .github/workflows/       ← CI + weekly scoring + nightly pipeline
├── docker-compose.yml       ← Default: API → Supabase
├── docker-compose.local.yml ← Optional: API → local PostgreSQL
└── docs/adr/DECISIONS.md    ← Architecture decisions
```

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | System health check |
| `GET /repos?tier=starter&min_score=60` | Ranked repositories with score breakdown |
| `GET /repos/{id}` | Single repo with full explanation |
| `GET /issues?quality=high` | AI mentor hints for issues |
| `GET /issues/{id}` | Full step-by-step guide for one issue |

---

*GitNova — Your AI mentor for meaningful open-source contributions.*
