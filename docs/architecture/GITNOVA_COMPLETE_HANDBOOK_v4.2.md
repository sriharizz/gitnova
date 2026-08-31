# GitNova v4.2 — The Complete Handbook
> **Unified Source of Truth: Product Vision + Architecture + Engineering + Data Flow**
>
> Version: 4.2
> Last Updated: 2026-07-28
>
> This is the only document you need. Read it before every sprint.

---

## Table of Contents

1. [The Product Vision](#1-the-product-vision)
2. [Critical Findings](#2-critical-findings)
3. [Technology Stack (Validated)](#3-technology-stack-validated)
4. [Complete System Architecture](#4-complete-system-architecture)
5. [Repository Qualification Engine (The Differentiator)](#5-repository-qualification-engine-the-differentiator)
6. [Complete Data Flow](#6-complete-data-flow)
7. [Database Design](#7-database-design)
8. [API Design (FastAPI)](#8-api-design-fastapi)
9. [12-Sprint Implementation Plan](#9-12-sprint-implementation-plan)
10. [Docker & Containerization](#10-docker--containerization)
11. [GitHub Actions CI/CD](#11-github-actions-cicd)
12. [Testing Strategy](#12-testing-strategy)
13. [Monitoring, Logging & Observability](#13-monitoring-logging--observability)
14. [Project Structure (End State)](#14-project-structure-end-state)
15. [Interview Guide](#15-interview-guide)
16. [Learning Roadmap](#16-learning-roadmap)
17. [Appendices](#17-appendices)

---

## 1. The Product Vision

### What GitNova Is

**GitNova is an AI Open Source Mentor.**

It does not merely explain issues. It intelligently discovers, scores, and vets repositories for contributor-friendliness **before** surfacing a single issue. Then it retrieves actual source code, grounds an LLM in that code, and generates a step-by-step fix blueprint.

### What GitNova Answers

1. **Which repositories are worth contributing to?** *(Repository Qualification Engine → Contribution Success Score)*
2. **Which issue should I choose?** *(Issue Intelligence + RAG)*
3. **Why is it suitable for me?** *(Competition scoring + difficulty estimation)*
4. **What code should I read?** *(Hybrid RAG retrieval)*
5. **How should I approach solving it?** *(LLM Mentor with file-level guidance)*

### The Mental Model Shift

| | Before (v3→v4) | After (v4.2) |
|---|---|---|
| **Pipeline start** | Curated repo list → scan issues | GitHub Search → qualify repos → rank → scan issues |
| **What we build first** | Issue explainer | Repository qualification + mentoring |
| **Differentiator** | RAG + multi-model cascade | **Contribution Success Score + RAG + LLM Mentor** |
| **Interview hook** | "I built a RAG pipeline" | "I built a system that qualifies repos on contributor-friendliness before surfacing issues" |

### The North Star Metric

Every architectural decision should optimize for one outcome:

> **Increase the probability that a beginner successfully makes and merges their first meaningful pull request.**

This is GitNova's North Star Metric.

Every feature should directly or indirectly improve this probability. If a feature does not contribute to this objective, reconsider whether it belongs in V1.

### The North Star Question

Before accepting any design decision, ask:

> **"Does this make GitNova more memorable than a generic RAG project?"**

If not, reject or simplify it.

### Product Principles

GitNova should behave like an experienced open-source mentor. The system should:

- **Reduce uncertainty.** Tell the user exactly which repo, which issue, which file.
- **Build confidence.** Start with easy wins, then progress to harder challenges.
- **Explain every recommendation.** Transparency builds trust.
- **Prefer transparency over black-box decisions.** Every score has a visible breakdown.
- **Help users learn rather than simply complete tasks.** Teach, don't just answer.
- **Recommend repositories where users are likely to succeed,** not repositories that are merely famous.
- **Encourage gradual progression** from beginner projects to complex open-source ecosystems.
- **Optimize for long-term contributor growth,** not only the first merged PR. A slightly harder issue that teaches testing or architecture is worth more than an easy typo fix.

The user's confidence is as important as the recommendation quality.

### What GitNova Is NOT

GitNova is **NOT**:
- a GitHub search engine
- a generic chatbot
- an issue summarizer
- an autonomous coding agent
- an automatic PR generator
- a replacement for learning software engineering

GitNova **IS**:
- an AI Open Source Mentor
- a repository qualification system
- an issue intelligence platform
- a code-aware guidance system
- a contribution confidence builder

### Engineering Philosophy

Preserve the existing architecture whenever possible. Do not redesign components unless necessary.

Avoid adding: agents, LangGraph, fine-tuning, Kubernetes, Redis, or microservices — unless there is a clear engineering justification.

Simplicity is preferred over unnecessary sophistication.

### User Experience Goal

The user should feel:

> **"I finally know where I should contribute."**

rather than:

> *"Here is another GitHub issue."*

That emotional outcome is the real product goal.

### Landing Page Framing

The landing page should **NOT** say:
> *"AI-powered repository intelligence."*

It should say:
> **"Find your first successful open-source contribution with confidence."**

---

## 2. Critical Findings

These are validated issues that will undermine you in interviews if not fixed.

### 🔴 CRITICAL: NVIDIA NIM Free Tier Is Unstable

**Your claim:** NVIDIA NIM is primary LLM provider (Gemma 4, Llama 3.3).

**Reality:** NVIDIA explicitly states free tier is for **"testing models only."** Developer forums are filled with reports of frequent 429 errors. A moderator said: *"if you are using the free-tier API, you have absolutely no right to demand a rate limit increase."*

**Fix:** Groq → PRIMARY (30 RPM, 1,000/day, stable). OpenRouter → FALLBACK (50/day, 20 RPM). NVIDIA NIM → emergency only. Use **LiteLLM** as single abstraction layer.

### 🔴 CRITICAL: No FastAPI Service — Script, Not System

Your architecture has no API layer. Everything is a GitHub Actions batch script. Recruiters expect to see FastAPI, request/response handling, and service boundaries.

**Fix:** Add FastAPI service layer with 4 endpoints: `/repos`, `/issues`, `/issues/{id}`, `/health`.

### 🟡 HIGH: Supabase Pauses After 7 Days

Free tier projects auto-pause after 7 days of inactivity. Your database goes offline.

**Fix:** Add `keepalive.yml` GitHub Actions workflow that pings Supabase every 3 days.

### 🟡 HIGH: "Fine-Tuned DeBERTa" — Credibility Risk

If you did not actually fine-tune DeBERTa on a labeled dataset, do not claim you did. Interviewers will ask for F1 scores, training data size, LoRA vs full fine-tuning.

**Fix:** Say *"zero-shot classification with confidence thresholding."* That is still impressive and defensible.

### 🟡 HIGH: 4-Model Cascade Is Over-Engineered

Hard to explain, slower, and adds no value over 2 providers with smart retry.

**Fix:** Groq primary → retry with tweaked prompt → OpenRouter fallback. 2 providers, not 4.

### 🟢 GOOD: GitHub Actions Minutes Are FREE

GitHub Actions is **completely free and unlimited** for **public repositories.** The 2,000-minute limit only applies to private repos.

---

## 3. Technology Stack (Validated)

Every technology below has been validated against: free-tier limits, rate limits, interview value, maintenance burden, and migration path.

### 3.1 Backend: FastAPI

| Question | Answer |
|----------|--------|
| **Why?** | Async-native, auto OpenAPI docs, Pydantic validation. Industry standard for Python ML services. |
| **Alternatives** | Flask (no native async), Django (too heavy), Fastify (JS — wrong ecosystem) |
| **Free tier** | Open source — free forever |
| **Interview value** | **HIGH** — every AI Engineer role expects FastAPI |

### 3.2 Database: PostgreSQL + pgvector

| Question | Answer |
|----------|--------|
| **Why?** | Industry-standard vector extension. Hybrid search (vector + FTS) is production-grade. |
| **Hosted** | Supabase (free: 500MB DB, 5GB egress, **pauses after 7 days**) |
| **Local** | Docker `pgvector/pgvector:pg16` — one command |
| **Interview value** | **HIGH** — pgvector + HNSW + RRF is a genuine differentiator |

**⚠️ Supabase free tier reality:** 500MB fills up fast. 5GB egress/month burns quickly. No backups. Auto-pause after 7 days. Use keepalive job. Monitor aggressively.

### 3.3 LLM Providers: Groq + OpenRouter (via LiteLLM)

| Provider | Free Tier | RPM | RPD | Reliability | Role |
|----------|-----------|-----|-----|-------------|------|
| **Groq** | Free | 30 | 1,000/day | **HIGH** | **PRIMARY** |
| **OpenRouter** | 50 req/day | 20 | 50/day | MEDIUM | **FALLBACK** |
| **NVIDIA NIM** | 40 RPM | 40 | ~1,000/day | LOW | Emergency only |

**LiteLLM:** Single interface. One line of code switches providers. Automatic failover.

### 3.4 Embeddings: Jina Embeddings v2 (Local CPU)

| Question | Answer |
|----------|--------|
| **Why?** | 768-dim, code-optimized, runs on CPU. No API cost. No rate limits. |
| **Via** | `sentence-transformers` on GitHub Actions CPU |
| **Interview value** | **HIGH** — "I run embeddings locally to avoid vendor lock-in" |

### 3.5 Issue Classification: DeBERTa v3 Base (Zero-Shot)

| Question | Answer |
|----------|--------|
| **Why?** | Strong zero-shot classification. Good confidence scores. |
| **Fine-tuned?** | **Only say yes if you actually did.** Otherwise: zero-shot with threshold. |
| **Via** | `transformers` pipeline on CPU |

### 3.6 Repository Qualification Engine: Heuristics (No ML)

| Question | Answer |
|----------|--------|
| **Why?** | No labeled training data. Fully explainable. Zero cost. 90% of the value. |
| **What** | 5 pillars, 14 sub-metrics, weighted sum → score 0-100 |
| **Interview value** | **HIGH** — "I chose heuristics over ML because explainability beats black-box accuracy for this use case" |

### 3.7 Deployment: Render (Free) + GitHub Pages

| Platform | Free Tier | Best For |
|----------|-----------|----------|
| **Render** | 512MB RAM, sleeps after 15min | API service |
| **GitHub Pages** | Unlimited (public) | Frontend |

### 3.8 Containerization: Docker + Docker Compose

```bash
# Default: API only. Supabase is the database.
docker compose up
# → FastAPI on :8000 (connects to Supabase via DATABASE_URL)
# → Hot reload for dev

# Optional: full offline local dev (no Supabase required)
docker compose -f docker-compose.yml -f docker-compose.local.yml up
# → PostgreSQL + pgvector on :5432
# → FastAPI on :8000 (connects to local DB)
```

### 3.9 CI/CD: GitHub Actions

**Minutes are UNLIMITED for public repositories.** Split workflows:
- `ci.yml` — lint → type-check → test → build Docker
- `intelligence.yml` — weekly repo discovery + scoring
- `nightly.yml` — issue scanning + RAG + LLM
- `index.yml` — manual repo re-indexing
- `keepalive.yml` — ping Supabase every 3 days

---

## 4. Complete System Architecture

### 4.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GITNOVA v4.2                                   │
│               Repository Qualification Engine → LLM Mentor                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 1: DATA SOURCES                                                      │
│  ─────────────────────                                                      │
│    ┌────────────┐  ┌────────────┐  ┌────────────┐                           │
│    │ GitHub     │  │ Groq       │  │ OpenRouter │                           │
│    │ REST API   │  │ (Primary   │  │ (Fallback  │                           │
│    │            │  │  LLM)      │  │  LLM)      │                           │
│    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                           │
│          │               │               │                                  │
│  LAYER 2: PIPELINES (GitHub Actions)                                        │
│  ───────────────────────────────────                                        │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  WEEKLY: Repository Qualification                                    │   │
│  │                                                                      │   │
│  │  GitHub Search API → Fetch metadata → Heuristic scorer → Rank       │   │
│  │       │                    │                  │            │         │   │
│  │       ▼                    ▼                  ▼            ▼         │   │
│  │  100 candidates    10 API calls/repo      5 pillars    Top 30       │   │
│  │  per query         per repo               0-100        per tier     │   │
│  │                                                                      │   │
│  │  Output: repos table with score, tier, is_active                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ON-DEMAND: Code Indexing                                            │   │
│  │                                                                      │   │
│  │  Clone repo → Tree-sitter chunk → Jina embed → Upsert to PG         │   │
│  │                                                                      │   │
│  │  Output: snapshots + code_chunks tables                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  EVERY 12 HOURS: Issue Pipeline                                      │   │
│  │                                                                      │   │
│  │  Scan issues → DeBERTa classify → Competition score → RAG retrieve  │   │
│  │  → LLM generate → Validate → Quality score → Publish                │   │
│  │                                                                      │   │
│  │  Output: issues table with ai_hint, quality_score, quality_grade    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LAYER 3: API SERVICE (FastAPI — Always On)                                 │
│  ──────────────────────────────────────────                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  GET /repos?tier=starter&min_score=60        → Ranked repo list     │   │
│  │  GET /repos/{id}                             → Repo detail + score  │   │
│  │  GET /issues?tier=starter&quality=high       → Filtered issues      │   │
│  │  GET /issues/{id}                            → Full AI mentor hint  │   │
│  │  GET /health                                 → System status        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LAYER 4: DATABASE                                                          │
│  ─────────────────                                                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PostgreSQL + pgvector                                               │   │
│  │                                                                      │   │
│  │  repos          ← Centerpiece: score, tier, raw_metrics             │   │
│  │  snapshots      ← Code snapshots per repo                           │   │
│  │  code_chunks    ← Embedded source code (768-dim vectors)            │   │
│  │  issues         ← GitHub issues + AI hints                          │   │
│  │  pipeline_runs  ← Execution logs                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LAYER 5: LOCAL ML MODELS (CPU)                                             │
│  ──────────────────────────────                                             │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                  │
│  │ DeBERTa v3 Base         │  │ Jina Embeddings v2      │                  │
│  │ Issue classifier        │  │ Code embedder             │                  │
│  └─────────────────────────┘  └─────────────────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Responsibilities

| Component | Technology | Responsibility |
|-----------|-----------|--------------|
| **API Service** | FastAPI + Uvicorn | HTTP interface: repos, issues, health |
| **Repo Qualification Worker** | Python script (weekly cron) | Discover repos, score, rank, store |
| **Issue Worker** | Python script (12-hour cron) | Scan issues, classify, RAG, LLM, validate, publish |
| **Indexer** | Python script (on-demand) | Clone, chunk, embed, store |
| **Database** | PostgreSQL + pgvector | All data storage + vector search |
| **LLM Client** | LiteLLM | Unified interface to Groq + OpenRouter |
| **Embedder** | sentence-transformers | Local Jina embeddings (768-dim) |
| **Classifier** | transformers + DeBERTa | Zero-shot issue classification |

---

## 5. Repository Qualification Engine (The Differentiator)

> **Terminology:** The internal engine is called the **Repository Qualification Engine**. The user never interacts with it directly. Instead, users experience its output through a **Contribution Success Score** (0-100) and transparent explanations of why each repository was recommended.

### 5.1 Philosophy: Heuristics, Not ML

**Do NOT build a complex ML model for repo scoring.**

Why:
- No labeled training data (who rates repos 0-100?)
- Heuristics are **explainable** — every point is defensible
- Heuristics are **zero-cost** — no training, no GPU
- Heuristics are **maintainable** — tweak weights without retraining

**The rule:** If a weighted sum of GitHub metadata delivers 90% of the value, use it.

### 5.2 Data Collection (All From GitHub API)

| Data | API Endpoint | What It Tells Us |
|------|-------------|-------------------|
| Basic metadata | `GET /repos/{owner}/{repo}` | Stars, forks, language, license, pushed_at |
| Issues (90 days) | `GET /repos/{owner}/{repo}/issues?state=all&since=...` | Velocity, close time |
| Pull requests | `GET /repos/{owner}/{repo}/pulls?state=all` | Merge rate, merge time |
| File check | `GET /repos/{owner}/{repo}/contents/CONTRIBUTING.md` | Has contributing guide? |
| File check | `GET /repos/{owner}/{repo}/contents/CODE_OF_CONDUCT.md` | Has code of conduct? |
| File check | `GET /repos/{owner}/{repo}/contents/README.md` | Documentation proxy |
| Labels | `GET /repos/{owner}/{repo}/labels` | Has good-first-issue? |
| Contributors | `GET /repos/{owner}/{repo}/contributors` | Community health |
| Releases | `GET /repos/{owner}/{repo}/releases` | Release recency |

**All free. No GraphQL needed. No paid tier.**

### 5.3 The Five Pillars (0-100 Points)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTRIBUTION SUCCESS SCORE (0-100)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PILLAR 1: ACTIVITY                    20 points                            │
│  ───────────────────                                                        │
│  recent_push_score      = max(0, 1 - days_since_push/30) × 10               │
│  issue_velocity_score   = min(issues_closed_30d / 10, 1) × 10               │
│                                                                             │
│  PILLAR 2: WELCOME SIGNALS             25 points  ★ HIGHEST WEIGHT          │
│  ─────────────────────────────────────                                      │
│  has_contributing_md          = 10 if present, else 0                       │
│  has_good_first_issue_label   = 10 if present, else 0                       │
│  has_code_of_conduct          = 5 if present, else 0                        │
│  NOTE: stars removed — star count is not a welcome signal.                  │
│                                                                             │
│  PILLAR 3: RESPONSIVENESS              20 points                            │
│  ────────────────────────                                                   │
│  pr_merge_rate        = (merged_prs / total_prs) × 10                       │
│  fast_merge_time      = 5 if avg_merge_days < 7, else 0                     │
│  issue_response_time  = 5 if median_close_days < 2, else 0                  │
│                                                                             │
│  PILLAR 4: DOCUMENTATION               15 points                            │
│  ───────────────────────                                                    │
│  readme_quality       = min(readme_length / 5000, 1) × 10                   │
│  has_license          = 5 if any OSI license present, else 0                │
│                                                                             │
│  PILLAR 5: HEALTH                      20 points                            │
│  ────────────────                                                           │
│  permissive_license   = 5 if MIT/Apache-2.0/BSD-3-Clause/ISC               │
│  manageable_backlog   = 5 if open_issues < 100                              │
│  healthy_community    = 5 if contributors > 5                               │
│  recent_release       = 5 if release within 90 days                         │
│                                                                             │
│  ════════════════════════════════════════════                               │
│  TOTAL = sum of all pillars (0-100)                                         │
│  GRADE: >=70 excellent | >=50 good | >=30 fair | <30 avoid                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Tier Assignment

Tier represents **onboarding complexity**, gated by a minimum quality score.
Stars do NOT define tier — they are one weak input to the complexity estimate.
A 20K-star repo with excellent docs can be a Starter.
A 500-star undocumented codebase can be Established.

```python
def assign_tier(score: float, complexity: float) -> Optional[str]:
    if score < 30:        # Below quality floor — don't recommend
        return None
    if complexity < 35:   # Easy to enter — first PR in a day
        return "starter"
    elif complexity < 65: # Moderate — requires reading docs/architecture
        return "growing"
    else:                 # Large-scale — deep investment required
        return "established"
```

**Onboarding complexity** is a separate 0-100 estimate computed alongside the
Contribution Success Score. It uses GitHub API signals (stars, backlog size,
community size, documentation) in Sprint 3. Sprint 5 will enhance it with
file_count, total_loc, and directory_depth from cloned repository structure.

### 5.5 Why These Weights?

| Pillar | Weight | Justification |
|--------|--------|---------------|
| **Welcome Signals** | 25% | If a repo doesn't WANT contributors, nothing else matters. CONTRIBUTING.md, good-first-issue labels, and Code of Conduct are explicit intent signals. Stars removed — they measure popularity, not welcome intent. |
| **Responsiveness** | 20% | A PR sitting unmerged for months destroys morale. Fast merge times = alive, engaged community. |
| **Activity** | 20% | Dead repos waste everyone's time. Recent commits prove the project breathes. |
| **Health** | 20% | License permissiveness, community size, manageable backlog = long-term viability. |
| **Documentation** | 15% | Has any license (trust signal) + README quality. Code of Conduct moved to Welcome Signals where it belongs. |

### 5.6 Full Scorer Implementation

```python
# backend/app/intelligence/scorer.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class RepoMetrics:
    stars: int
    forks: int
    open_issues_count: int
    days_since_push: int
    issues_closed_30d: int
    prs_merged_30d: int
    prs_total_30d: int
    avg_pr_merge_days: Optional[float]
    median_issue_close_days: Optional[float]
    has_contributing_md: bool
    has_code_of_conduct: bool
    has_good_first_issue_label: bool
    readme_length: int
    contributor_count: int
    license_spdx: Optional[str]
    days_since_release: Optional[int]

@dataclass
class RepoScore:
    total: float                          # Contribution Success Score (0-100)
    grade: str                            # excellent | good | fair | avoid
    tier: Optional[str]                   # starter | growing | established | None
    breakdown: dict                       # per-pillar scores
    explanation: List[str]                # deterministic human-readable explanations
    complexity_estimate: float            # 0-100 (PROVISIONAL until Sprint 5)
    complexity_signals: dict              # inputs to complexity estimate
    metrics: RepoMetrics

# Full implementation: backend/app/intelligence/scorer.py
# Key design decisions:
#   - Pillar 2 renamed to "Welcome Signals"; stars removed; CoC added
#   - Pillar 4 Documentation: has_license replaces CoC
#   - Tier uses complexity_estimate, not stars
#   - complexity_estimate is provisional (Sprint 5 will add file_count, LOC)
#   - explanation is deterministic — no LLM
# See scorer.py for full implementation and test_scorer.py for 52 tests.
```

---

## 6. Complete Data Flow

### 6.1 One Repository's Journey

```
GitHub Search API → Fetch 10 metadata calls/repo → Heuristic Scorer 
  → Score 0-100 → Grade → Tier → Store in repos table 
  → (if active) Clone → Chunk → Embed → Store in code_chunks 
  → (every 12h) Scan issues → For each: Classify → RAG → LLM → Validate 
  → Publish to issues table → Serve via GET /issues
```

### 6.2 One Issue's Journey (Full Detail)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ISSUE JOURNEY (v4.2)                                  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DISCOVER    GitHub Search API finds repo "pallets/flask"                │
│  2. SCORE       Heuristic engine: 85.6/100, grade=excellent, tier=advanced  │
│  3. ACTIVATE    Store in repos table with is_active=TRUE                    │
│  4. INDEX       Clone → tree-sitter chunk → Jina embed → code_chunks        │
│  5. SCAN        Fetch issue #2847: "Bug: session cookie not expiring"       │
│  6. CLASSIFY    DeBERTa: bug=0.89 (>0.30 threshold) → PASS                 │
│  7. COMPETE     accessibility=0.125, freshness=0.933 → medium               │
│  8. RETRIEVE    Embed issue → vector search + FTS → RRF fusion              │
│                 Top result: src/sessions.py (similarity 0.91)                │
│  9. GENERATE    Prompt: system + issue + code → Groq llama-3.3-70b          │
│                 Returns JSON: goal, files, changes, estimated_time          │
│  10. VALIDATE   ✓ Has file paths  ✓ Files exist  ✓ No banned verbs         │
│  11. SCORE      Quality: 100/100, grade=high                                │
│  12. PUBLISH    Upsert to issues table                                      │
│  13. SERVE      GET /issues/2847 returns complete AI mentor hint            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 The Two Independent Paths

| Path | When | What | Calls LLM? | Duration |
|------|------|------|------------|----------|
| **Worker** (batch) | Weekly (repos) + 12h (issues) | Heavy lifting: scoring, embedding, LLM | **YES** | 30min–2h |
| **API** (service) | 24/7 | Reads pre-computed data from DB | **NO** | ~20ms |

**Critical insight:** The API never calls an LLM. It only reads from the database. The LLM calls happen in the batch worker. This is why the API is fast, cheap, and stays online on free tiers.

---

## 7. Database Design

### 7.1 Schema

```sql
-- Repositories (centerpiece of v4.2)
CREATE TABLE repos (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name           TEXT NOT NULL UNIQUE,
    stars               INTEGER DEFAULT 0,
    forks               INTEGER DEFAULT 0,
    language            TEXT,
    description         TEXT,
    license_spdx        TEXT,
    score               FLOAT DEFAULT 0,
    score_grade         TEXT CHECK (score_grade IN ('excellent', 'good', 'fair', 'avoid')),
    score_breakdown     JSONB DEFAULT '{}',
    tier                TEXT CHECK (tier IN ('starter', 'growing', 'established')),
    is_active           BOOLEAN DEFAULT TRUE,
    raw_metrics         JSONB DEFAULT '{}',
    first_discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_intelligence_at TIMESTAMPTZ,
    last_indexed_at     TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_repos_score ON repos(score DESC) WHERE is_active = TRUE;
CREATE INDEX idx_repos_tier ON repos(tier) WHERE is_active = TRUE;
CREATE INDEX idx_repos_language ON repos(language) WHERE is_active = TRUE;

-- Code snapshots
CREATE TABLE snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id         UUID NOT NULL REFERENCES repos(id),
    commit_sha      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    chunk_count     INTEGER DEFAULT 0,
    embedding_model TEXT DEFAULT 'jinaai/jina-embeddings-v2-base-code',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repo_id, commit_sha)
);

-- Code chunks
CREATE TABLE code_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id     UUID NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    repo_id         UUID NOT NULL REFERENCES repos(id),
    file_path       TEXT NOT NULL,
    symbol_name     TEXT,
    content         TEXT NOT NULL,
    embedding       VECTOR(768),
    fts             TSVECTOR,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_code_chunks_embedding ON code_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_code_chunks_fts ON code_chunks USING GIN (fts);

-- Issues
CREATE TABLE issues (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id             UUID NOT NULL REFERENCES repos(id),
    github_issue_id     BIGINT NOT NULL,
    title               TEXT NOT NULL,
    body                TEXT,
    state               TEXT DEFAULT 'open',
    labels              TEXT[],
    comments_count      INTEGER DEFAULT 0,
    reactions_count     INTEGER DEFAULT 0,
    assignee            TEXT,
    issue_created_at    TIMESTAMPTZ,
    ai_hint             TEXT,
    quality_score       INTEGER CHECK (quality_score BETWEEN 0 AND 100),
    quality_grade       TEXT CHECK (quality_grade IN ('high', 'medium', 'low')),
    model_provider      TEXT,
    retrieval_method    TEXT DEFAULT 'none',
    difficulty          TEXT,
    estimated_time      TEXT,
    is_published        BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(repo_id, github_issue_id)
);

CREATE INDEX idx_issues_repo ON issues(repo_id);
CREATE INDEX idx_issues_published ON issues(is_published, quality_score DESC);

-- Pipeline runs
CREATE TABLE pipeline_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type        TEXT NOT NULL,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    repos_processed INTEGER DEFAULT 0,
    items_found     INTEGER DEFAULT 0,
    items_published INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'running',
    error_log       TEXT
);
```

### 7.2 Hybrid Search Functions

```sql
CREATE OR REPLACE FUNCTION match_chunks_vector(
    query_embedding VECTOR(768),
    match_threshold FLOAT,
    match_count INT,
    repo_filter UUID[]
)
RETURNS TABLE(id UUID, file_path TEXT, symbol_name TEXT, content TEXT, similarity FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT cc.id, cc.file_path, cc.symbol_name, cc.content,
           1 - (cc.embedding <=> query_embedding) AS similarity
    FROM code_chunks cc
    JOIN snapshots s ON cc.snapshot_id = s.id
    WHERE s.status = 'active' AND cc.repo_id = ANY(repo_filter)
      AND 1 - (cc.embedding <=> query_embedding) > match_threshold
    ORDER BY cc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION match_chunks_fts(
    query_text TEXT,
    match_count INT,
    repo_filter UUID[]
)
RETURNS TABLE(id UUID, file_path TEXT, symbol_name TEXT, content TEXT, rank FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT cc.id, cc.file_path, cc.symbol_name, cc.content,
           ts_rank_cd(cc.fts, plainto_tsquery('english', query_text), 32)::FLOAT AS rank
    FROM code_chunks cc
    JOIN snapshots s ON cc.snapshot_id = s.id
    WHERE s.status = 'active' AND cc.repo_id = ANY(repo_filter)
      AND cc.fts @@ plainto_tsquery('english', query_text)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;
```

---

## 8. API Design (FastAPI)

### 8.1 Endpoints

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="GitNova API", version="4.2.0")

# ─── Health ─────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Check database and LLM connectivity."""
    ...

# ─── Repositories ───────────────────────────────────────
class RepoOut(BaseModel):
    id: str
    full_name: str
    tier: str
    score: float
    score_grade: str
    score_breakdown: dict              # per-pillar scores {activity, beginner, ...}
    score_explanation: List[str]       # human-readable reasons
    stars: int
    language: Optional[str]
    description: Optional[str]
    last_scored_at: Optional[datetime]

@app.get("/repos", response_model=List[RepoOut])
async def list_repos(
    tier: Optional[str] = Query(None, enum=["starter", "growing", "established"]),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    language: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List scored and ranked repositories."""
    ...

@app.get("/repos/{repo_id}", response_model=RepoOut)
async def get_repo(repo_id: str):
    """Get single repo with full score breakdown."""
    ...

# ─── Issues ─────────────────────────────────────────────
class IssueOut(BaseModel):
    id: str
    repo_name: str
    repo_tier: str                     # which tier this repo belongs to
    repo_score: float                  # Contribution Success Score
    title: str
    ai_hint: Optional[str]
    quality_score: int
    quality_grade: str
    difficulty: Optional[str]
    estimated_time: Optional[str]
    competition_level: Optional[str]   # low / medium / high
    freshness_label: Optional[str]     # "Updated 3 days ago", not raw number
    created_at: datetime

@app.get("/issues", response_model=List[IssueOut])
async def list_issues(
    tier: Optional[str] = Query(None, enum=["starter", "growing", "established"]),
    quality: Optional[str] = Query(None, enum=["high", "medium", "low"]),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List published issues with filters."""
    ...

@app.get("/issues/{issue_id}", response_model=IssueOut)
async def get_issue(issue_id: str):
    """Get single issue with full AI mentor hint."""
    ...
```

### 8.2 Why These Endpoints Matter

When asked "What does your API do?" you say:

> *"GitNova's FastAPI service exposes scored repositories and AI-generated contribution hints. `/repos?tier=starter&min_score=60` returns contributor-friendly repositories ranked by our heuristic score. `/issues` returns filtered hints with quality grades. `/health` checks database and LLM connectivity — our GitHub Actions keepalive pings this to keep Supabase awake."*

---

## 9. 12-Sprint Implementation Plan

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           12-SPRINT PLAN (6 WEEKS)                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  WEEK 1                                                                          │
│  ├── Sprint 0 (Days 1-3):     FOUNDATION                                        │
│  │   Scaffold, Docker Compose, pre-commit, README                               │
│  │   OUTPUT: docker compose up works                                            │
│  │                                                                              │
│  ├── Sprint 1 (Days 4-6):     DATABASE                                          │
│  │   Schema, migrations, connection pool, seed data                             │
│  │   OUTPUT: Tables created, can query repos/issues/chunks                      │
│  │                                                                              │
│  └── Sprint 2 (Days 7-9):     GITHUB CLIENT + DISCOVERY                         │
│      Async GitHub client, search API, rate limit handling                      │
│      OUTPUT: Can discover repos from GitHub Search API                         │
│                                                                                  │
│  WEEK 2                                                                          │
│  ├── Sprint 3 (Days 10-13):   REPO QUALIFICATION ENGINE ★ DIFFERENTIATOR        │
│  │   Heuristic scoring engine, metadata collection, tier assignment             │
│  │   OUTPUT: Contribution Success Score (0-100) with per-pillar breakdown       │
│  │                                                                              │
│  └── Sprint 4 (Days 14-16):   REPOSITORY RANKING + API                          │
│      Rank by Contribution Success Score, store in DB, /repos endpoints         │
│      OUTPUT: GET /repos?tier=starter returns repos with score + explanation     │
│                                                                                  │
│  WEEK 3                                                                          │
│  ├── Sprint 5 (Days 17-20):   CODE INDEXING                                     │
│  │   Tree-sitter chunker, Jina embedder, upsert to code_chunks                  │
│  │   OUTPUT: One repo fully indexed with embeddings                             │
│  │                                                                              │
│  └── Sprint 6 (Days 21-23):   RAG RETRIEVAL                                     │
│      Vector search, FTS, RRF fusion                                            │
│      OUTPUT: Given issue text, retrieves relevant code chunks                  │
│                                                                                  │
│  WEEK 4                                                                          │
│  ├── Sprint 7 (Days 24-27):   LLM MENTOR + LiteLLM                              │
│  │   Prompt engineering, provider failover, JSON output parsing                 │
│  │   OUTPUT: Mentor hint explaining WHY this issue suits a beginner,            │
│  │   exactly which files/functions to change, and approach to learn from        │
│  │                                                                              │
│  └── Sprint 8 (Days 28-30):   ISSUE INTELLIGENCE                                │
│      DeBERTa classify, competition scoring, filtering                          │
│      OUTPUT: Issues ranked by accessibility and freshness                      │
│                                                                                  │
│  WEEK 5                                                                          │
│  ├── Sprint 9 (Days 31-34):   VALIDATION + QUALITY + OUTCOME TRACKING           │
│  │   Rule engine, file existence check, quality scoring, PR outcome tracker     │
│  │   OUTPUT: Bad outputs caught, good outputs scored, outcome tracking ready    │
│  │                                                                              │
│  └── Sprint 10 (Days 35-37):  FASTAPI COMPLETE                                  │
│      All endpoints, error handling, health checks                              │
│      OUTPUT: Full API running at localhost:8000                                │
│                                                                                  │
│  WEEK 6                                                                          │
│  ├── Sprint 11 (Days 38-40):  CI/CD + GITHUB ACTIONS                            │
│  │   5 workflows: CI, intelligence, nightly, index, keepalive                   │
│  │   OUTPUT: Pipeline runs automatically on schedule                            │
│  │                                                                              │
│  └── Sprint 12 (Days 41-42):  POLISH + DOCUMENTATION                            │
│      README, API docs, LinkedIn post (frontend deferred to post-backend)       │
│      OUTPUT: Backend complete, documented, deployed, ready for frontend         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Sprint 3 Detail: Repository Qualification Engine

```
Sprint 3: Repository Qualification Engine (Days 10-13)
══════════════════════════════════════════════════════

Day 10: Data Collection
───────────────────────
• Implement GitHub metadata fetcher
  - Batch API calls efficiently (respect rate limits)
  - Collect: stars, forks, issues, PRs, files, labels, contributors, releases
• Store raw metrics in repos.raw_metrics (JSONB)

Day 11: Scoring Engine
──────────────────────
• Implement heuristic scorer (5 pillars, 14 sub-metrics)
• Unit tests for scorer with known inputs
  - Test: "flask" should score > 70 (has CONTRIBUTING.md, active)
  - Test: "dead-repo" should score < 30 (no commits in 180 days)

Day 12: Tier Assignment + Store
───────────────────────────────
• Implement tier assignment logic
• Connect: discovery → scoring → tier → store in DB
• Test: score 85 + stars 66K → tier="established"

Day 13: Integration
───────────────────
• End-to-end: discover 5 repos → score → store → query via raw SQL
• Verify: DB has repos with correct scores and tiers
```

### 9.1 Implementation Rules (For AI-Assisted Development)

When implementing sprints with an AI IDE:

1. **Explain** the implementation plan before writing code.
2. **List** all files to be created or modified.
3. **Implement** one sprint at a time.
4. **Run tests** before considering a sprint complete.
5. **Stop** after finishing each sprint and wait for review.
6. **Never** continue automatically to the next sprint.
7. **Never** modify files unrelated to the current sprint.
8. **Follow** sprint boundaries strictly.

---

## 10. Docker & Containerization

### 10.1 docker-compose.yml (Default — Supabase)

**Default configuration connects FastAPI to Supabase cloud. No local DB required.**

```yaml
version: "3.8"

services:
  api:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}          # Supabase connection string
      - GROQ_API_KEY=${GROQ_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./backend/app:/app/app                # hot reload in dev
    restart: unless-stopped
```

### 10.1b docker-compose.local.yml (Optional — Offline Dev)

**Only use this if you want to develop without a Supabase connection.**

```yaml
version: "3.8"

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: gitnova
      POSTGRES_PASSWORD: gitnova
      POSTGRES_DB: gitnova
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    environment:
      - DATABASE_URL=postgresql+asyncpg://gitnova:gitnova@db:5432/gitnova
    depends_on:
      - db

volumes:
  pgdata:
```

### 10.2 Dockerfile (Multi-Stage)

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY backend/app ./app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 10.3 One Command

```bash
git clone https://github.com/yourusername/gitnova.git
cd gitnova
cp .env.example .env
# Edit .env with your API keys
docker compose up --build
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

## 11. GitHub Actions CI/CD

### 11.1 Workflows

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI** | `ci.yml` | Push/PR to main | Lint → type-check → test → build Docker |
| **Repository Qualification** | `intelligence.yml` | Weekly (Sundays 00:00 UTC) | Discover repos → score → rank → store |
| **Issue Pipeline** | `nightly.yml` | Every 12 hours (6:30 AM/PM UTC) | Scan issues → classify → RAG → LLM → publish |
| **Code Indexing** | `index.yml` | Manual trigger | Clone → chunk → embed → store |
| **Supabase Keepalive** | `keepalive.yml` | Every 3 days | Ping DB to prevent auto-pause |

### 11.2 ci.yml

```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install ruff mypy
      - run: ruff check backend/
      - run: ruff format --check backend/   # formatting check
      - run: mypy backend/app/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install pip-audit
      - run: pip-audit -r backend/requirements.txt  # dependency CVE scan

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements-dev.txt
      - run: pytest backend/tests/ -v --cov=app --cov-report=xml
        env:
          DATABASE_URL: ""  # Unit tests mock the DB — no real DB needed in CI

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -f backend/Dockerfile -t gitnova-api .
```

### 11.3 intelligence.yml

```yaml
name: Weekly Repository Qualification
on:
  schedule:
    - cron: "0 0 * * 0"  # Every Sunday at midnight UTC
  workflow_dispatch:

jobs:
  score:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: python -m backend.app.intelligence.run
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 11.4 nightly.yml

```yaml
name: Nightly Issue Pipeline
on:
  schedule:
    - cron: "30 6,18 * * *"
  workflow_dispatch:

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: python -m backend.app.pipeline.run
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 11.5 keepalive.yml

```yaml
name: Supabase Keepalive
on:
  schedule:
    - cron: "0 0 */3 * *"

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: |
          curl -s "${{ secrets.SUPABASE_URL }}/rest/v1/repos?select=id&limit=1" \
            -H "apikey: ${{ secrets.SUPABASE_KEY }}" > /dev/null
```

---

## 12. Testing Strategy

### 12.1 Test Pyramid

```
        /\
       /  \
      / E2E \      5% — End-to-end pipeline test
     /─────────\
    / Integration \  15% — API + DB + mock external APIs
   /───────────────\
  /     Unit        \ 80% — Individual functions, pure logic
 /─────────────────────\
```

### 12.2 Key Unit Tests

```python
# test_scorer.py
import pytest
from app.intelligence.scorer import RepositoryScorer, RepoMetrics

@pytest.mark.parametrize("metrics,expected_score", [
    # Flask-like: active, contributing, responsive
    (RepoMetrics(
        stars=66000, forks=17000, open_issues_count=50,
        days_since_push=5, issues_closed_30d=25,
        prs_merged_30d=18, prs_total_30d=20,
        avg_pr_merge_days=2.5, median_issue_close_days=3,
        has_contributing_md=True, has_code_of_conduct=True,
        has_good_first_issue_label=True, readme_length=12000,
        contributor_count=150, license_spdx="BSD-3-Clause",
        days_since_release=40
    ), 85),
    # Dead repo: no commits, no contributors
    (RepoMetrics(
        stars=100, forks=5, open_issues_count=200,
        days_since_push=180, issues_closed_30d=0,
        prs_merged_30d=0, prs_total_30d=0,
        avg_pr_merge_days=None, median_issue_close_days=None,
        has_contributing_md=False, has_code_of_conduct=False,
        has_good_first_issue_label=False, readme_length=200,
        contributor_count=1, license_spdx=None,
        days_since_release=None
    ), 10),
])
def test_repo_scoring(metrics, expected_score):
    scorer = RepositoryScorer()
    result = scorer.score(metrics)
    assert abs(result.total - expected_score) < 5
```

### 12.3 Test Coverage Target

**Aim for 70%+ coverage.** Focus on:
- Scoring engine (highest impact, pure logic, easy to test)
- Validation rules
- RRF fusion scoring
- API endpoint contracts
- GitHub client retry logic

Do NOT aim for 100% — testing trivial getters is a waste of time.

---

## 13. Monitoring, Logging & Observability

### 13.1 Structured Logging

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("gitnova")
handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s %(stage)s %(duration_ms)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Usage:
logger.info("stage_completed", extra={
    "stage": "repository_scoring",
    "repos_processed": 30,
    "duration_ms": 4500
})
```

**Why JSON?** In production, logs go to observability tools (Datadog, CloudWatch). JSON is parseable. Plain text is not.

### 13.2 Pipeline Run Tracking

Every pipeline run inserts into `pipeline_runs`:

```python
# At pipeline start
run_id = await db.execute(
    "INSERT INTO pipeline_runs (run_type, status) VALUES ('issue_scan', 'running') RETURNING id"
)

# At pipeline end
await db.execute(
    "UPDATE pipeline_runs SET status = 'success', finished_at = NOW(), "
    "repos_processed = $1, items_found = $2, items_published = $3 WHERE id = $4",
    30, 450, 85, run_id
)
```

This lets you track success/failure history, throughput, and debug failures.

---

## 14. Project Structure (End State)

```
gitnova/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── intelligence.yml
│       ├── nightly.yml
│       ├── index.yml
│       └── keepalive.yml
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   ├── repos.py
│   │   │   ├── issues.py
│   │   │   └── health.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── health.py
│   │   │
│   │   ├── clients/
│   │   │   ├── github.py
│   │   │   └── llm.py
│   │   │
│   │   ├── intelligence/           ← Repository Qualification Engine
│   │   │   ├── __init__.py
│   │   │   ├── scorer.py
│   │   │   ├── discover.py
│   │   │   ├── collector.py
│   │   │   └── run.py
│   │   │
│   │   ├── pipeline/
│   │   │   ├── runner.py
│   │   │   ├── scanner.py
│   │   │   ├── classifier.py
│   │   │   ├── retriever.py
│   │   │   ├── generator.py
│   │   │   └── validator.py
│   │   │
│   │   ├── indexer/
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   └── indexer.py
│   │   │
│   │   └── db/
│   │       ├── client.py
│   │       ├── models.py
│   │       └── queries.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   ├── test_scorer.py
│   │   ├── test_retrieval.py
│   │   ├── test_validation.py
│   │   └── test_github_client.py
│   │
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── docker-compose.yml              ← Default: API → Supabase
├── docker-compose.local.yml        ← Optional: API → local PostgreSQL
├── .env.example
├── .pre-commit-config.yaml
├── README.md
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    ├── AI_IDE_PROMPTS.md
    └── adr/                        ← Architecture Decision Records
        ├── 0001-why-fastapi.md
        ├── 0002-why-supabase.md
        ├── 0003-why-pgvector.md
        └── 0004-why-litellm.md
```

---

## 15. Interview Guide

### 15.1 The 60-Second Pitch

> *"GitNova helps developers find their first successful open-source contribution with confidence. Most tools just show you a list of issues and say 'good luck.' GitNova does something different: it first scores every repository on contributor-friendliness — looking at maintainer responsiveness, PR merge times, and explicit signals like CONTRIBUTING.md and good-first-issue labels. Only repos with a Contribution Success Score of 40+ are even considered. Then it uses a RAG pipeline with hybrid vector + full-text search in PostgreSQL pgvector, grounds an LLM in actual source code, and generates a step-by-step fix blueprint telling you exactly which file and function to change. The entire stack is zero-cost: Groq for inference, Supabase for vector storage, GitHub Actions for orchestration, and everything runs in Docker with a FastAPI service layer."*

### 15.2 The Architecture Explanation (3-5 Minutes)

**Draw this on a whiteboard:**

1. **"GitNova has two independent paths that share a database."**
2. **"The Worker path runs on GitHub Actions. It has two jobs:"**
   - Weekly: Discover repos from GitHub Search API, score them with a heuristic engine across 5 pillars, rank them, and store.
   - Every 12 hours: Scan issues, classify with DeBERTa, retrieve code with RAG, generate hints via Groq, validate, and publish.
3. **"The API path is a FastAPI service running on Render."**
   - `/repos?tier=starter&min_score=60` returns scored, ranked repos.
   - `/issues` returns pre-computed AI mentor hints.
   - `/health` checks DB + LLM connectivity.
4. **"For resilience, we use LiteLLM with Groq primary and OpenRouter fallback."**
5. **"Everything runs in Docker. One command: `docker compose up`."**

### 15.3 Expected Questions

**Q: "Why score repos before looking at issues?"**
> *"Because sending a beginner to a project where PRs sit unmerged for 6 months is worse than sending them nowhere. We score on five pillars: Activity, Beginner-Friendliness, Responsiveness, Documentation, and Health. Beginner-Friendliness is weighted highest because signals like CONTRIBUTING.md are explicit proof maintainers invest in onboarding. A repo scoring below 40 is filtered out entirely."*

**Q: "Why heuristics instead of ML for repo scoring?"**
> *"Three reasons. First, I have no labeled training data. Second, heuristics are fully explainable — I can tell you exactly why a repo scored 85. An ML model is a black box. Third, heuristics are zero-cost — no training, no GPU. If a simpler solution delivers 90% of the value, I choose it."*

**Q: "How do you handle GitHub API rate limits?"**
> *"Authenticated users get 5,000 requests/hour. I track the X-RateLimit-Remaining header and implement exponential backoff. For repository qualification, I only score 30 candidates per week — well within limits. I also cache raw metrics and only re-fetch what changed."*

**Q: "What makes GitNova different from goodfirstissue.dev?"**
> *"goodfirstissue.dev shows a static list of repos with good-first-issue labels. It doesn't tell you if maintainers merge PRs, if the project is dead, or if documentation exists. GitNova scores repos on five dimensions of contributor-friendliness, ranks them, and only then surfaces issues. Plus we ground every AI hint in actual source code via RAG — no other tool does that."*

**Q: "What would you change at 10,000 users?"**
> *"Three things: (1) Move from GitHub Actions cron to Celery + Redis for horizontal scaling. (2) Add a read replica for DB to separate ingestion from queries. (3) Consider Pinecone or Weaviate if pgvector hits throughput limits. But for 0 to 1, pgvector + GitHub Actions is the right choice."*

### 15.4 Red Flags to Avoid

❌ **Don't say:** *"I fine-tuned DeBERTa"* (unless you actually did)
✅ **Say:** *"I use DeBERTa v3 base for zero-shot classification with confidence thresholding."*

❌ **Don't say:** *"I use a 4-model LLM cascade"*
✅ **Say:** *"I use LiteLLM with Groq as primary and OpenRouter as fallback for resilience."*

❌ **Don't say:** *"It's deployed on Supabase"*
✅ **Say:** *"The API is containerized with Docker and deployed on Render. The database is hosted on Supabase."*

---

## 16. Learning Roadmap

By the end of GitNova v4.2, you should explain these cold:

### Core Concepts (Must Know)

| Concept | Where GitNova Uses It | Interview Angle |
|---------|----------------------|-----------------|
| **Heuristic scoring** | Repository Qualification Engine (5 pillars) | "I chose explainable heuristics over black-box ML" |
| **RAG** | Code retrieval → LLM prompt | "Ground the model in actual source code to reduce hallucination" |
| **Vector embeddings** | Jina v2 → pgvector | "768-dim code-optimized vectors for semantic search" |
| **Hybrid search** | Vector + FTS + RRF | "Combine semantic and lexical search without hyperparameter tuning" |
| **HNSW index** | pgvector approximate NN | "O(log n) queries for read-heavy RAG workloads" |
| **LLM prompt engineering** | Structured JSON output | "Constrain output to JSON schema for reliable parsing" |
| **Provider fallback** | LiteLLM: Groq → OpenRouter | "Resilience without architectural complexity" |
| **Async I/O** | FastAPI + httpx | "Concurrent API calls without blocking" |
| **Connection pooling** | asyncpg | "Efficient database access under load" |
| **CI/CD** | 5 GitHub Actions workflows | "Automated testing, scoring, and deployment" |
| **Docker** | Multi-stage Dockerfile | "One command for reproducible environments" |

### Deeper Dives (Interview Differentiators)

| Topic | Study Resource |
|-------|---------------|
| **RRF (Reciprocal Rank Fusion)** | Paper: "Reciprocal Rank Fusion outperforms Condorcet" |
| **pgvector internals** | HNSW vs IVFFlat on pgvector GitHub |
| **Tree-sitter parsing** | tree-sitter.dev docs |
| **Structured generation** | Outlines, JSON mode, function calling |
| **Observability** | OpenTelemetry, structured logging patterns |

### What to Skip

| Topic | Why Skip | When to Learn |
|-------|----------|---------------|
| Kubernetes | Overkill for one dev | Team of 3+ |
| Kafka | No streaming volume | 10K+ events/sec |
| Microservices | Single codebase is simpler | Team of 5+ |
| Custom model training | Zero-shot works fine | Labeled data + GPU budget |
| GraphQL | REST is sufficient | Complex nested queries needed |

---

## 17. Appendices

### Appendix A: Free-Tier Summary

| Service | Free Tier | Limitations | GitNova Usage |
|---------|-----------|-------------|---------------|
| GitHub Actions | Unlimited minutes (public) | 6h job timeout | CI + all pipelines |
| Supabase | 500MB DB, 5GB egress | Pauses after 7 days | Hosted PostgreSQL |
| Groq | 30 RPM, 1,000/day | No SLA | Primary LLM |
| OpenRouter | 50/day (20 RPM) | 1,000/day with $10 | Fallback LLM |
| NVIDIA NIM | 40 RPM | Testing only | Emergency fallback |
| Render | 512MB RAM, sleeps 15min | Cold starts | API hosting |
| GitHub Pages | Unlimited (public) | Static only | Frontend |
| Docker | Free | — | Local dev |
| HuggingFace | Free download | — | Local models |

### Appendix B: Cost Summary

| Service | Cost |
|---------|------|
| GitHub Actions (public) | **₹0** |
| Supabase (free) | **₹0** |
| Groq (free) | **₹0** |
| OpenRouter (free) | **₹0** |
| Render (free) | **₹0** |
| GitHub Pages | **₹0** |
| **TOTAL** | **₹0** |

### Appendix C: The One-Line Mission

> **GitNova helps developers find their first successful open-source contribution with confidence — using a Contribution Success Score that qualifies repositories, RAG-grounded LLM mentoring that pinpoints exact files to change, and production-grade Python engineering, entirely on free-tier infrastructure.**

### Appendix D: Final Validation Checklist

Before finalizing any modification, ask yourself:

1. Does this improve the probability of a beginner making a successful, merged contribution?
2. Does this make GitNova more memorable than a generic RAG application?
3. Can the developer explain every architectural decision in an AI Engineer interview?
4. Is this still realistic for one developer using free-tier services?

If the answer to any question is "No", revise the design.

Preserve engineering excellence. Strengthen product thinking. Do not increase unnecessary complexity.

---

*End of GitNova v4.2 Complete Handbook*

*This is your single source of truth. Read it before every sprint.*
