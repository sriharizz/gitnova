# GitNova v4.2 — Product Vision Shift: Repository Qualification Engine First
> **The missing differentiator that transforms GitNova from "issue finder" to "AI Open Source Mentor"**
>
> Last Updated: 2026-07-28
>
> Based on: GitNova_Project_Intent_Context_for_Kimi.md

---

## Table of Contents

1. [The Product Vision Shift](#1-the-product-vision-shift)
2. [Why the Repository Qualification Engine Is the Differentiator](#2-why-the-repository-qualification-engine-is-the-differentiator)
3. [Repository Qualification Engine Design](#3-repository-qualification-engine-design)
4. [Updated Master Pipeline](#4-updated-master-pipeline)
5. [Updated Data Flow](#5-updated-data-flow)
6. [Updated Sprint Plan](#6-updated-sprint-plan)
7. [Repository Scoring Engine (Full Specification)](#7-repository-scoring-engine-full-specification)
8. [Updated Database Schema](#8-updated-database-schema)
9. [Interview Narrative — How to Sell This](#9-interview-narrative--how-to-sell-this)
10. [What Stays the Same from v4](#10-what-stays-the-same-from-v4)

---

## 1. The Product Vision Shift

### Old Mental Model (v3 → v4)

> "GitNova finds open-source issues and explains them with AI."

Pipeline: **Curated repo list** → Scan issues → Classify → RAG → LLM → Publish

Problem: Every other tool does this. goodfirstissue.dev, up-for-grabs.net, CodeTriage. You're just adding AI explanation on top.

### New Mental Model (v4.2)

> **"GitNova helps developers find their first successful open-source contribution with confidence. It intelligently discovers, qualifies, and ranks repositories for contributor-friendliness BEFORE surfacing a single issue."**

Pipeline: **GitHub** → **Repository Discovery** → **Repository Qualification (scoring)** → **Repository Ranking** → **Issue Discovery** → **Issue Intelligence** → **Hybrid RAG** → **LLM Mentor** → **Validation** → **API**

This is the key insight: **Before telling a beginner which issue to fix, prove the repository is worth fixing.**

### North Star Metric

Every architectural decision should optimize for one outcome:

> **Increase the probability that a beginner successfully makes and merges their first meaningful pull request.**

This is GitNova's North Star Metric. Every feature should directly or indirectly improve this probability. If a feature does not contribute to this objective, reconsider whether it belongs in V1.

### Product Principles

GitNova should behave like an experienced open-source mentor. The system should:

- **Reduce uncertainty.** Tell the user exactly which repo, which issue, which file.
- **Build confidence.** Start with easy wins, then progress to harder challenges.
- **Explain every recommendation.** Transparency builds trust.
- **Prefer transparency over black-box decisions.** Every score has a visible breakdown.
- **Help users learn rather than simply complete tasks.** Teach, don't just answer.
- **Recommend repositories where users are likely to succeed,** not repositories that are merely famous.
- **Encourage gradual progression** from beginner projects to complex open-source ecosystems.

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

### User-Facing vs Internal Terminology

| Internal Name | User Sees | Why |
|---|---|---|
| Repository Qualification Engine | Contribution Success Score (0-100) | Users care about "Can I succeed here?" not "repository intelligence" |
| Heuristic Scorer | Score breakdown with explanations | Transparency builds trust |
| Tier Assignment | Starter → Growing → Advanced labels | Guides the progression journey |

### Landing Page Framing

The landing page should **NOT** say:
> *"AI-powered repository intelligence."*

It should say:
> **"Find your first successful open-source contribution with confidence."**

---

## 2. Why the Repository Qualification Engine Is the Differentiator

### The Problem GitNova Solves (That No One Else Does)

A beginner wants to contribute. They find "good first issue" labels on kubernetes/kubernetes. They try. They fail. Why?

- 50,000 open issues. Overwhelming.
- PRs take 3 months to merge. Demotivating.
- No CONTRIBUTING.md. Confusing.
- Maintainers don't respond to questions. Isolating.
- The codebase is 2M lines. Intimidating.

**Current tools say:** *"Here's an issue. Good luck."*

**GitNova says:** *"This repository has a Contribution Success Score of 87/100. It has a CONTRIBUTING.md, maintainers merge PRs in 4 days on average, and 60% of issues have responses within 48 hours. Here's a starter-level issue with low competition and exactly which files to read."*

### Competitive Matrix (Updated)

| Capability | goodfirstissue | up-for-grabs | CodeTriage | GitNova v3 | **GitNova v4.2** |
|---|---|---|---|---|---|
| Issue discovery | ✅ Static | ✅ Static | ✅ Email | ✅ Automated | ✅ Automated |
| AI explanation | ❌ | ❌ | ❌ | ✅ LLM | ✅ LLM Mentor |
| Code grounding (RAG) | ❌ | ❌ | ❌ | ✅ Hybrid | ✅ Hybrid |
| **Repo qualification** | ❌ | ❌ | ❌ | ❌ | **✅ Heuristic scoring** |
| **Contribution Success Score** | ❌ | ❌ | ❌ | ❌ | **✅ 0-100** |
| **Maintainer responsiveness** | ❌ | ❌ | ❌ | ❌ | **✅ PR merge time** |
| Beginner tiering | ❌ | ❌ | ❌ | ❌ | **✅ Starter/Mid/Advanced** |

**The moat:** No other platform evaluates whether a repository is actually welcoming to contributors BEFORE recommending its issues.

---

## 3. Repository Qualification Engine Design

### 3.1 Philosophy: Heuristics, Not ML

**Do NOT build a complex ML model for repo scoring.**

Why:
- You have no labeled training data ("this repo is 7.3/10 contributor-friendly")
- A heuristic model is explainable — every point is defensible in an interview
- A heuristic model is maintainable — you can tweak weights without retraining
- A heuristic model is fast — no GPU, no inference time

**The rule:** If a weighted sum of GitHub metadata delivers 90% of the value, use it.

### 3.2 What Data We Collect (All From GitHub API)

| Data Source | API Endpoint | What It Tells Us |
|-------------|-------------|-------------------|
| Basic metadata | `GET /repos/{owner}/{repo}` | Stars, forks, language, pushed_at, open_issues_count, license |
| Issues (last 90 days) | `GET /repos/{owner}/{repo}/issues?state=all&since=...` | Issue velocity, close time distribution |
| Pull requests | `GET /repos/{owner}/{repo}/pulls?state=all` | PR merge rate, merge time |
| File check | `GET /repos/{owner}/{repo}/contents/CONTRIBUTING.md` | Has contributing guide? |
| File check | `GET /repos/{owner}/{repo}/contents/CODE_OF_CONDUCT.md` | Has code of conduct? |
| File check | `GET /repos/{owner}/{repo}/contents/README.md` | README length, documentation quality proxy |
| Labels | `GET /repos/{owner}/{repo}/labels` | Has "good first issue", "help wanted", "beginner-friendly"? |
| Contributors | `GET /repos/{owner}/{repo}/contributors` | Community health, bus factor |
| Commits | `GET /repos/{owner}/{repo}/commits?since=...` | Commit frequency, recent activity |

**All of this is free via GitHub REST API.** No GraphQL required. No paid tier needed.

### 3.3 The Scoring Dimensions (5 Pillars)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTRIBUTION SUCCESS SCORE                                │
│                              (0 - 100 points)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PILLAR 1: ACTIVITY (20 points)                                              │
│  ──────────────────────────────                                              │
│  Measures: Is this project alive?                                            │
│                                                                              │
│  + recent_push_score      (0-10)  max(0, 1 - days_since_push / 30) × 10    │
│  + issue_velocity_score   (0-10)  min(issues_closed_30d / 10, 1) × 10      │
│                                                                              │
│  Why: A repo with no commits in 90 days is dead. Don't send beginners there. │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PILLAR 2: BEGINNER_FRIENDLINESS (25 points) — HIGHEST WEIGHT                │
│  ────────────────────────────────────────────────────────────                │
│  Measures: Does this repo WANT beginners?                                    │
│                                                                              │
│  + has_contributing_md          (0-10)  10 if present, 0 if absent           │
│  + has_good_first_issue_labels  (0-10)  10 if label exists, 0 if not         │
│  + is_small_enough              (0-5)   5 if stars < 10,000                  │
│                                                                              │
│  Why: CONTRIBUTING.md and good-first-issue labels are explicit signals       │
│  that maintainers invest in onboarding newcomers.                            │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PILLAR 3: MAINTAINER_RESPONSIVENESS (20 points)                             │
│  ───────────────────────────────────────────────                             │
│  Measures: Will anyone actually review my PR?                                │
│                                                                              │
│  + pr_merge_rate          (0-10)  (merged_prs / total_prs) × 10              │
│  + fast_merge_time        (0-5)   5 if avg_merge_time < 7 days              │
│  + issue_response_time    (0-5)   5 if median_first_response < 48h          │
│                                                                              │
│  Why: A repo where PRs sit unmerged for 6 months destroys beginner morale.   │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PILLAR 4: DOCUMENTATION (15 points)                                         │
│  ──────────────────────────────────                                          │
│  Measures: Can I figure out how to contribute without asking?                │
│                                                                              │
│  + readme_quality         (0-10)  min(readme_length / 5000, 1) × 10         │
│  + has_code_of_conduct    (0-5)   5 if present                               │
│                                                                              │
│  Why: A 200-character README means "figure it out yourself."                 │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PILLAR 5: HEALTH (20 points)                                                │
│  ────────────────────────────                                                │
│  Measures: Is this a stable, healthy project?                                │
│                                                                              │
│  + permissive_license     (0-5)   5 if MIT/Apache/BSD/GPL                   │
│  + manageable_backlog     (0-5)   5 if open_issue_ratio < 0.3               │
│  + healthy_community      (0-5)   5 if contributor_count > 5                 │
│  + recent_release         (0-5)   5 if release within 90 days               │
│                                                                              │
│  Why: A repo with 5,000 open issues and 1 contributor is a graveyard.        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

FINAL SCORE = sum of all pillars (0-100)
GRADE: >= 70 = "Excellent", >= 50 = "Good", >= 30 = "Fair", < 30 = "Avoid"
```

### 3.4 Tier Assignment (Automatic)

After scoring, repos are auto-assigned to tiers:

```python
def assign_tier(repo_score: int, stars: int, language: str) -> str:
    """
    Tier assignment based on score + size + language ecosystem.
    """
    if repo_score >= 60 and stars < 5_000:
        return "starter"      # Small, welcoming, perfect for first PR
    elif repo_score >= 50 and stars < 50_000:
        return "mid"          # Active, structured, good for portfolio
    elif repo_score >= 40:
        return "advanced"     # Large, complex, for experienced contributors
    else:
        return None           # Don't track this repo
```

---

## 4. Updated Master Pipeline

### 4.1 The New Pipeline (Repository Qualification First)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    GITNOVA v4.2 — MASTER PIPELINE                             │
│              (Repository Qualification Engine → LLM Mentor)                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: REPOSITORY LIFECYCLE (Runs Weekly)                                 │
│  ───────────────────────────────────────────                                 │
│                                                                              │
│  ┌─────────────┐    ┌─────────────────────┐    ┌─────────────────────────┐   │
│  │  DISCOVER   │ →  │  QUALIFICATION      │ →  │  RANK & STORE           │   │
│  │             │    │  (Score 0-100)      │    │                         │   │
│  │ GitHub      │    │                     │    │ Sort by score DESC       │   │
│  │ Search API: │    │ • Activity (20)     │    │ Take top 10 per tier     │   │
│  │             │    │ • Beginner (25)     │    │ Mark as is_active=TRUE   │   │
│  │ stars:100.. │    │ • Responsive (20)   │    │ Insert/Update repos table│   │
│  │ 50000       │    │ • Documentation (15)│    │                         │   │
│  │ language:py │    │ • Health (20)       │    │                         │   │
│  │ pushed:>30d │    │                     │    │                         │   │
│  │             │    │ Fetch 30 candidates │    │                         │   │
│  │ Returns:    │    │ Score each          │    │                         │   │
│  │ 100 repos   │    │ Store in DB         │    │                         │   │
│  └─────────────┘    └─────────────────────┘    └─────────────────────────┘   │
│         ↑                                                                    │
│         │                                                                    │
│    Also: Manual additions via repos.yaml (override)                          │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  PHASE 2: INDEXING LIFECYCLE (Runs After Repo Discovery, or Manual)          │
│  ─────────────────────────────────────────────────────────────────────       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │ For each ACTIVE repo:                                               │     │
│  │                                                                     │     │
│  │   1. Clone repo (shallow, depth=1)                                  │     │
│  │   2. Parse with tree-sitter → extract functions, classes            │     │
│  │   3. Chunk: max 512 tokens per chunk                                │     │
│  │   4. Embed with Jina v2 (local CPU) → 768-dim vectors               │     │
│  │   5. Upsert to code_chunks table with HNSW index                    │     │
│  │   6. Create snapshot record (commit SHA, chunk count)               │     │
│  │                                                                     │     │
│  │   [Only for STARTER repos: index ENTIRE codebase]                   │     │
│  │   [For MID/ADVANCED: index top 50 core files]                       │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  PHASE 3: ISSUE LIFECYCLE (Runs Every 12 Hours)                              │
│  ─────────────────────────────────────────────────                             │
│                                                                              │
│  ┌─────────────┐    ┌─────────────────────┐    ┌─────────────────────────┐   │
│  │  SCAN       │ →  │  CLASSIFY & RANK    │ →  │  RETRIEVE & GENERATE    │   │
│  │             │    │                     │    │                         │   │
│  │ For each    │    │ DeBERTa:            │    │ Embed issue text        │   │
│  │ ACTIVE repo:│    │   bug/feature/Q     │    │ Vector search (HNSW)    │   │
│  │             │    │                     │    │ FTS search (GIN)        │   │
│  │ Fetch 15    │    │ Filter:             │    │ RRF fusion              │   │
│  │ newest open │    │   conf > 0.30       │    │                         │   │
│  │ issues      │    │   not question      │    │ Build prompt:           │   │
│  │             │    │                     │    │   system + issue + code │   │
│  │             │    │ Score competition:  │    │                         │   │
│  │             │    │   accessibility     │    │ Call LLM (Groq → OR)    │   │
│  │             │    │   freshness         │    │ Parse JSON output       │   │
│  │             │    │                     │    │                         │   │
│  │             │    │ Take top 10/repo    │    │ Validate:               │   │
│  │             │    │                     │    │   files exist?          │   │
│  │             │    │                     │    │   no banned verbs?      │   │
│  │             │    │                     │    │   valid JSON?           │   │
│  │             │    │                     │    │                         │   │
│  │             │    │                     │    │ Score quality (0-100)   │   │
│  │             │    │                     │    │ Grade: high/medium/low  │   │
│  │             │    │                     │    │                         │   │
│  │             │    │                     │    │ Upsert to issues table  │   │
│  └─────────────┘    └─────────────────────┘    └─────────────────────────┘   │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────── │
│                                                                              │
│  PHASE 4: SERVING LIFECYCLE (Always On)                                      │
│  ─────────────────────────────────────                                       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  FastAPI Service (Render free tier)                                 │     │
│  │                                                                     │     │
│  │  GET /repos?tier=starter&min_score=60        →  Ranked repo list    │     │
│  │  GET /repos/{id}                             →  Repo detail + score │     │
│  │  GET /issues?tier=starter&quality=high       →  Filtered issues     │     │
│  │  GET /issues/{id}                            →  Full AI mentor hint │     │
│  │  GET /health                                 →  System status       │     │
│  │                                                                     │     │
│  │  Frontend (GitHub Pages) calls these endpoints                      │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Pipeline Schedule

| Phase | Frequency | Trigger | Duration |
|-------|-----------|---------|----------|
| **Repository Discovery** | Weekly | GitHub Actions cron (Sundays 00:00 UTC) | ~30 min |
| **Repository Qualification** | Weekly | Same job as discovery | ~15 min |
| **Indexing** | On-demand or after discovery | Manual trigger or auto for new repos | ~1-2 hours |
| **Issue Scanning** | Every 12 hours | GitHub Actions cron (6:30 AM/PM UTC) | ~1-2 hours |
| **API Serving** | 24/7 | Render web service | Always on |
| **Keepalive** | Every 3 days | GitHub Actions cron | ~1 min |
| **Outcome Tracking** | Weekly | GitHub Actions cron | ~15 min |

---

## 5. Updated Data Flow

### 5.1 One Repository's Journey (The New Story)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    REPOSITORY JOURNEY: GitHub → Ranked Mentor                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STEP 1: DISCOVER                                                            │
│  ─────────────                                                               │
│  GitHub Search API query:                                                    │
│  "stars:100..50000 language:python pushed:>2026-06-25 good-first-issues:>1" │
│                                                                              │
│  Found candidate: "pallets/flask"                                            │
│  Stars: 66,000 → Actually too big for starter, but let's score it           │
│                                                                              │
│  STEP 2: FETCH METADATA                                                      │
│  ─────────────────────                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  GitHub API calls (all batched, ~10 requests):                        │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask                                             │   │
│  │    → stars: 66,000 | forks: 17,000 | language: Python                │   │
│  │    → open_issues: 50 | pushed_at: "2026-07-20" (5 days ago)          │   │
│  │    → license: { "spdx_id": "BSD-3-Clause" }                          │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/issues?state=all&since=2026-04-25          │   │
│  │    → 30 issues in last 90 days                                       │   │
│  │    → 25 closed, 5 open                                               │   │
│  │    → Median close time: 3 days                                       │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/pulls?state=all&since=2026-04-25           │   │
│  │    → 20 PRs in last 90 days                                          │   │
│  │    → 18 merged, 2 closed                                             │   │
│  │    → Merge rate: 90%                                                 │   │
│  │    → Avg merge time: 2.5 days                                        │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/contents/CONTRIBUTING.md                   │   │
│  │    → Status: 200 (exists, 3,200 bytes)                               │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/contents/CODE_OF_CONDUCT.md                │   │
│  │    → Status: 200 (exists, 1,500 bytes)                               │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/contents/README.md                         │   │
│  │    → Size: 12,000 bytes                                              │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/labels                                     │   │
│  │    → Contains: "good first issue", "help wanted", "beginner-friendly"│   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/contributors                               │   │
│  │    → 150 contributors                                                │   │
│  │                                                                       │   │
│  │  GET /repos/pallets/flask/releases?per_page=1                        │   │
│  │    → Latest: 2026-06-15 (40 days ago)                                │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  STEP 3: SCORE (Heuristic Engine — No ML)                                    │
│  ─────────────────────────────────────────                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                                                                       │   │
│  │  PILLAR 1 — ACTIVITY (20 pts):                                        │   │
│  │    recent_push: 5 days ago → 1 - 5/30 = 0.83 × 10 = 8.3 pts         │   │
│  │    issue_velocity: 25 closed / 30 days = 0.83 × 10 = 8.3 pts        │   │
│  │    Subtotal: 16.6 / 20                                                │   │
│  │                                                                       │   │
│  │  PILLAR 2 — BEGINNER_FRIENDLINESS (25 pts):                           │   │
│  │    has_contributing_md: YES → 10 pts                                  │   │
│  │    has_good_first_issue: YES → 10 pts                                 │   │
│  │    is_small: stars=66K > 10K → 0 pts                                  │   │
│  │    Subtotal: 20 / 25                                                  │   │
│  │                                                                       │   │
│  │  PILLAR 3 — RESPONSIVENESS (20 pts):                                  │   │
│  │    pr_merge_rate: 18/20 = 90% × 10 = 9.0 pts                         │   │
│  │    fast_merge: 2.5 days < 7 days → 5 pts                              │   │
│  │    issue_response: median 3 days < 48h → 5 pts                        │   │
│  │    Subtotal: 19 / 20                                                  │   │
│  │                                                                       │   │
│  │  PILLAR 4 — DOCUMENTATION (15 pts):                                   │   │
│  │    readme: 12,000 / 5,000 = 1.0 × 10 = 10 pts                        │   │
│  │    has_coc: YES → 5 pts                                               │   │
│  │    Subtotal: 15 / 15                                                  │   │
│  │                                                                       │   │
│  │  PILLAR 5 — HEALTH (20 pts):                                          │   │
│  │    license: BSD-3-Clause (permissive) → 5 pts                         │   │
│  │    backlog: 50 open / (50+25 closed in 90d) = 0.40 → 0 pts           │   │
│  │    community: 150 > 5 → 5 pts                                         │   │
│  │    release: 40 days ago < 90 days → 5 pts                             │   │
│  │    Subtotal: 15 / 20                                                  │   │
│  │                                                                       │   │
│  │  ═══════════════════════════════════════                              │   │
│  │  TOTAL SCORE: 85.6 / 100  →  GRADE: EXCELLENT                         │   │
│  │  TIER: advanced (stars > 50K, but score > 40)                         │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  STEP 4: STORE                                                               │
│  ─────────────                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │  UPSERT INTO repos:                                                   │   │
│  │                                                                       │   │
│  │  id: <uuid>                                                           │   │
│  │  full_name: "pallets/flask"                                           │   │
│  │  tier: "advanced"                                                     │   │
│  │  score: 85.6                                                          │   │
│  │  score_grade: "excellent"                                             │   │
│  │  stars: 66000                                                         │   │
│  │  language: "Python"                                                   │   │
│  │  is_active: TRUE                                                      │   │
│  │                                                                       │   │
│  │  score_breakdown: {                                                   │   │
│  │    "activity": 16.6,                                                  │   │
│  │    "beginner": 20.0,                                                  │   │
│  │    "responsiveness": 19.0,                                            │   │
│  │    "documentation": 15.0,                                             │   │
│  │    "health": 15.0                                                     │   │
│  │  }                                                                    │   │
│  │                                                                       │   │
│  │  raw_metrics: {                                                       │   │
│  │    "days_since_push": 5,                                              │   │
│  │    "issues_closed_30d": 25,                                           │   │
│  │    "pr_merge_rate": 0.90,                                             │   │
│  │    "avg_pr_merge_days": 2.5,                                          │   │
│  │    "median_issue_close_days": 3,                                      │   │
│  │    "has_contributing_md": true,                                       │   │
│  │    "has_good_first_issue": true,                                      │   │
│  │    "contributor_count": 150,                                          │   │
│  │    "readme_length": 12000                                             │   │
│  │  }                                                                    │   │
│  │                                                                       │   │
│  │  last_intelligence_at: 2026-07-25 06:00:00                            │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  STEP 5: NOW AVAILABLE FOR ISSUE SCANNING                                    │
│  ────────────────────────────────────────                                    │
│  Since is_active=TRUE and tier="advanced", the nightly issue scanner        │
│  will include this repo and surface its issues with AI mentor hints.        │
│                                                                              │
│  GET /repos?tier=advanced&min_score=80                                      │
│  → Returns "pallets/flask" with score 85.6 and full breakdown               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Updated Sprint Plan (Repository Qualification Engine Integrated)

The sprint plan now puts the Repository Qualification Engine in the critical path.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              UPDATED 12-SPRINT PLAN                                  │
│                         (Repository Qualification First)                             │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Week 1                                                                              │
│  ├─ Sprint 0: FOUNDATION (Days 1-3)                                                 │
│  │   Scaffold, Docker Compose, pre-commit, README                                   │
│  │   OUTPUT: docker compose up works                                                │
│  │                                                                                  │
│  ├─ Sprint 1: DATABASE (Days 4-6)                                                   │
│  │   Schema (ALL tables), migrations, connection pool, seed data                    │
│  │   OUTPUT: Tables created, can query repos/issues/chunks                          │
│  │                                                                                  │
│  ├─ Sprint 2: GITHUB CLIENT + REPO DISCOVERY (Days 7-9)                            │
│  │   Async GitHub client, search API, rate limit handling                           │
│  │   OUTPUT: Can discover repos from GitHub Search API                              │
│  │                                                                                  │
│  Week 2                                                                              │
│  ├─ Sprint 3: REPO QUALIFICATION ENGINE (Days 10-13)  ★ CRITICAL                    │
│  │   Heuristic scoring engine, metadata collection, tier assignment                 │
│  │   OUTPUT: Given a repo name, produces score 0-100 with breakdown                 │
│  │                                                                                  │
│  ├─ Sprint 4: REPOSITORY RANKING + API (Days 14-16)                                │
│  │   Rank repos by score, store in DB, FastAPI /repos endpoints                     │
│  │   OUTPUT: GET /repos?tier=starter returns scored, ranked repos                   │
│  │                                                                                  │
│  Week 3                                                                              │
│  ├─ Sprint 5: CODE INDEXING (Days 17-20)                                           │
│  │   Tree-sitter chunker, Jina embedder, upsert to code_chunks                      │
│  │   OUTPUT: One repo fully indexed with embeddings                                 │
│  │                                                                                  │
│  ├─ Sprint 6: RAG RETRIEVAL (Days 21-23)                                           │
│  │   Vector search, FTS, RRF fusion                                                 │
│  │   OUTPUT: Given issue text, retrieves relevant code chunks                       │
│  │                                                                                  │
│  Week 4                                                                              │
│  ├─ Sprint 7: LLM MENTOR + LiteLLM (Days 24-27)                                    │
│  │   Prompt engineering, provider failover, JSON output parsing                     │
│  │   OUTPUT: Given issue + code, generates structured mentor hint                   │
│  │                                                                                  │
│  ├─ Sprint 8: ISSUE INTELLIGENCE (Days 28-30)                                      │
│  │   DeBERTa classify, competition scoring, filtering                               │
│  │   OUTPUT: Issues ranked by accessibility and freshness                           │
│  │                                                                                  │
│  Week 5                                                                              │
│  ├─ Sprint 9: VALIDATION + QUALITY (Days 31-34)                                    │
│  │   Rule engine, file existence check, quality scoring                             │
│  │   OUTPUT: Bad outputs caught, good outputs scored 0-100                          │
│  │                                                                                  │
│  ├─ Sprint 10: FASTAPI COMPLETE (Days 35-37)                                       │
│  │   All endpoints, error handling, health checks                                   │
│  │   OUTPUT: Full API running at localhost:8000                                     │
│  │                                                                                  │
│  Week 6                                                                              │
│  ├─ Sprint 11: CI/CD + GITHUB ACTIONS (Days 38-40)                                 │
│  │   4 workflows: CI, nightly, index, keepalive                                     │
│  │   OUTPUT: Pipeline runs automatically on schedule                                │
│  │                                                                                  │
│  ├─ Sprint 12: FRONTEND + POLISH (Days 41-42)                                      │
│  │   Simple HTML frontend, README, docs, LinkedIn post                              │
│  │   OUTPUT: Portfolio-ready project with live demo                                 │
│  │                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Sprint 3 Detail: Repository Qualification Engine (★ The Differentiator Sprint)

This is the most important sprint. Here's the breakdown:

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
• Implement heuristic scorer
  - 5 pillars: Activity, Beginner, Responsiveness, Documentation, Health
  - Each pillar has 2-4 sub-metrics with clear formulas
  - Total: 0-100 score
• Unit tests for scorer with known inputs

Day 12: Tier Assignment
───────────────────────
• Implement tier assignment logic
  - starter: score >= 60 AND stars < 5,000
  - mid: score >= 50 AND stars < 50,000
  - advanced: score >= 40
  - rejected: score < 40 (is_active = FALSE)
• Store score_breakdown as JSONB for transparency

Day 13: Integration + API
─────────────────────────
• Connect discovery → intelligence → ranking → store
• Add GET /repos endpoint with filters (tier, min_score, language)
• Test end-to-end: discover repo → score → store → query via API
```

---

## 7. Repository Scoring Engine (Full Specification)

### 7.1 Code Structure

```python
# backend/app/intelligence/scorer.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

@dataclass
class RepoMetrics:
    """Raw metrics collected from GitHub API."""
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
    """Computed Contribution Success Score."""
    total: float           # 0-100
    grade: str             # excellent | good | fair | avoid
    tier: str              # starter | mid | advanced | None
    breakdown: dict        # per-pillar scores
    metrics: RepoMetrics   # raw data

class RepositoryScorer:
    """Heuristic scorer — no ML, all explainable."""

    def score(self, metrics: RepoMetrics) -> RepoScore:
        activity = self._score_activity(metrics)
        beginner = self._score_beginner(metrics)
        responsiveness = self._score_responsiveness(metrics)
        documentation = self._score_documentation(metrics)
        health = self._score_health(metrics)

        total = activity + beginner + responsiveness + documentation + health
        grade = self._grade(total)
        tier = self._assign_tier(total, metrics.stars)

        return RepoScore(
            total=round(total, 1),
            grade=grade,
            tier=tier,
            breakdown={
                "activity": round(activity, 1),
                "beginner": round(beginner, 1),
                "responsiveness": round(responsiveness, 1),
                "documentation": round(documentation, 1),
                "health": round(health, 1),
            },
            metrics=metrics,
        )

    def _score_activity(self, m: RepoMetrics) -> float:
        recent_push = max(0, 1 - m.days_since_push / 30) * 10
        issue_velocity = min(m.issues_closed_30d / 10, 1) * 10
        return recent_push + issue_velocity

    def _score_beginner(self, m: RepoMetrics) -> float:
        contributing = 10 if m.has_contributing_md else 0
        labels = 10 if m.has_good_first_issue_label else 0
        small = 5 if m.stars < 10_000 else 0
        return contributing + labels + small

    def _score_responsiveness(self, m: RepoMetrics) -> float:
        merge_rate = (m.prs_merged_30d / max(m.prs_total_30d, 1)) * 10
        fast_merge = 5 if (m.avg_pr_merge_days or 999) < 7 else 0
        fast_response = 5 if (m.median_issue_close_days or 999) < 2 else 0
        return merge_rate + fast_merge + fast_response

    def _score_documentation(self, m: RepoMetrics) -> float:
        readme = min(m.readme_length / 5000, 1) * 10
        coc = 5 if m.has_code_of_conduct else 0
        return readme + coc

    def _score_health(self, m: RepoMetrics) -> float:
        permissive = 5 if m.license_spdx in {"MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0"} else 0
        manageable = 5 if m.open_issues_count < 100 else 0  # simplified
        community = 5 if m.contributor_count > 5 else 0
        recent_release = 5 if (m.days_since_release or 999) < 90 else 0
        return permissive + manageable + community + recent_release

    def _grade(self, total: float) -> str:
        if total >= 70: return "excellent"
        if total >= 50: return "good"
        if total >= 30: return "fair"
        return "avoid"

    def _assign_tier(self, total: float, stars: int) -> Optional[str]:
        if total >= 60 and stars < 5_000:
            return "starter"
        elif total >= 50 and stars < 50_000:
            return "mid"
        elif total >= 40:
            return "advanced"
        return None
```

### 7.2 Why These Weights?

| Pillar | Weight | Justification |
|--------|--------|---------------|
| **Beginner** | 25% (highest) | If a repo doesn't WANT beginners, nothing else matters. CONTRIBUTING.md and good-first-issue labels are explicit intent signals. |
| **Responsiveness** | 20% | A beginner's PR sitting unmerged for months is demotivating. Fast merge times prove the community is alive. |
| **Activity** | 20% | Dead repos waste everyone's time. Recent commits and issue velocity prove the project is alive. |
| **Health** | 20% | License, community size, and manageable backlog indicate long-term viability. |
| **Documentation** | 15% (lowest) | Important, but a small repo with good code can have minimal docs. Beginner-friendly repos need CONTRIBUTING.md more than a novel-length README. |

**In an interview:** *"I weighted Beginner-Friendliness highest because it's the strongest signal of contributor intent. A repo with a detailed CONTRIBUTING.md and good-first-issue labels is explicitly welcoming newcomers. Responsiveness is second because a fast merge cycle is the best feedback loop for beginners."*

---

## 8. Updated Database Schema

The `repos` table now becomes the centerpiece. Here's the updated schema:

```sql
-- Repositories with full intelligence
CREATE TABLE repos (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name           TEXT NOT NULL UNIQUE,       -- "pallets/flask"
    
    -- Basic metadata
    stars               INTEGER DEFAULT 0,
    forks               INTEGER DEFAULT 0,
    language            TEXT,
    description         TEXT,
    license_spdx        TEXT,
    
    -- Computed intelligence
    score               FLOAT DEFAULT 0,            -- 0-100
    score_grade         TEXT CHECK (score_grade IN ('excellent', 'good', 'fair', 'avoid')),
    score_breakdown     JSONB DEFAULT '{}',         -- per-pillar breakdown
    
    -- Tier and status
    tier                TEXT CHECK (tier IN ('starter', 'mid', 'advanced')),
    is_active           BOOLEAN DEFAULT TRUE,       -- FALSE if score < 40 or manually disabled
    
    -- Raw metrics (for transparency and debugging)
    raw_metrics         JSONB DEFAULT '{}',
    
    -- Timestamps
    first_discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_intelligence_at TIMESTAMPTZ,
    last_indexed_at     TIMESTAMPTZ,
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_repos_score ON repos(score DESC) WHERE is_active = TRUE;
CREATE INDEX idx_repos_tier ON repos(tier) WHERE is_active = TRUE;
CREATE INDEX idx_repos_language ON repos(language) WHERE is_active = TRUE;
CREATE INDEX idx_repos_grade ON repos(score_grade) WHERE is_active = TRUE;

-- Repository snapshots (code indexing)
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

-- Code chunks (unchanged)
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

-- Issues (unchanged from v4)
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
    difficulty          TEXT CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
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
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type            TEXT NOT NULL,              -- 'intelligence' | 'indexing' | 'issue_scan'
    started_at          TIMESTAMPTZ DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    repos_processed     INTEGER DEFAULT 0,
    items_found         INTEGER DEFAULT 0,
    items_published     INTEGER DEFAULT 0,
    status              TEXT DEFAULT 'running',
    error_log           TEXT
);
```

---

## 9. Interview Narrative — How to Sell This

### The 60-Second Pitch (Updated)

> *"GitNova helps developers find their first successful open-source contribution with confidence. Most tools just show you a list of issues and say 'good luck.' GitNova does something different: it first scores every repository on contributor-friendliness — looking at maintainer responsiveness, PR merge times, documentation quality, and explicit beginner-welcoming signals like CONTRIBUTING.md and good-first-issue labels. Only after a repo's Contribution Success Score reaches 40 or higher does GitNova even look at its issues. Then it uses a full RAG pipeline — hybrid vector + full-text search with HNSW indexes in PostgreSQL — to retrieve actual source code, grounds an LLM in that code, and generates a step-by-step fix blueprint telling you exactly which file and function to change. The entire stack is zero-cost: Groq for LLM inference, Supabase for vector storage, GitHub Actions for orchestration, and everything runs in Docker with a FastAPI service layer."*

### Expected Questions (Repository Qualification Angle)

**Q: "Why score repos before looking at issues?"**
> *"Because sending a beginner to a project where PRs sit unmerged for 6 months is worse than sending them nowhere. I score on five pillars: Activity, Beginner-Friendliness, Responsiveness, Documentation, and Health. Beginner-Friendliness is weighted highest because signals like CONTRIBUTING.md and good-first-issue labels are explicit proof the maintainers invest in onboarding newcomers. A repo that scores below 40 is filtered out entirely — we don't waste anyone's time."*

**Q: "Why heuristics instead of ML for repo scoring?"**
> *"Three reasons. First, I have no labeled training data — who decides a repo is '7.3 out of 10' contributor-friendly? Second, heuristics are fully explainable. I can tell you exactly why a repo scored 85: it has a CONTRIBUTING.md, maintainers merge PRs in 2.5 days on average, and it has good-first-issue labels. An ML model is a black box. Third, heuristics are zero-cost — no training, no GPU, no inference time. If a simpler solution delivers 90% of the value, I choose it."*

**Q: "How do you handle GitHub API rate limits with all this metadata fetching?"**
> *"I batch requests and respect the 5,000 requests/hour limit. For repository qualification, I only score 30 candidate repos per week — that's well within limits. I also cache raw metrics and only re-fetch what changed. For issue scanning, I fetch 15 issues per repo, which is also within limits. Everything has exponential backoff and graceful degradation."*

**Q: "What makes GitNova different from goodfirstissue.dev?"**
> *"goodfirstissue.dev shows you a static list of repos with good-first-issue labels. It doesn't tell you if the maintainers actually merge PRs, if the project is dead, or if the documentation exists. GitNova scores repos on five dimensions of contributor-friendliness, ranks them, and only then surfaces issues. Plus, we ground every AI hint in actual source code via RAG — no other tool does that."*

---

## 10. What Stays the Same from v4

The following from the original v4 handbook remains unchanged and strong:

| Component | Status | Why It Stays |
|-----------|--------|--------------|
| **RAG Pipeline** | ✅ Unchanged | Vector + FTS + RRF is already production-grade |
| **Hybrid Search** | ✅ Unchanged | HNSW index + GIN index + RRF fusion is the right design |
| **LLM Layer** | ✅ Unchanged | LiteLLM + Groq primary + OpenRouter fallback is correct |
| **Post-Validation** | ✅ Unchanged | Rule engine for hallucination catching is essential |
| **FastAPI Design** | ✅ Unchanged | 4-5 endpoints with Pydantic models is the right scope |
| **Docker Strategy** | ✅ Unchanged | Multi-stage Dockerfile + docker-compose is correct |
| **GitHub Actions CI/CD** | ✅ Unchanged | 4 workflows (CI, nightly, index, keepalive) is right |
| **Testing Pyramid** | ✅ Unchanged | 80% unit, 15% integration, 5% E2E |
| **Structured Logging** | ✅ Unchanged | JSON logs with trace IDs |
| **12-Sprint Timeline** | ✅ Adjusted | Sprint 3 is now Repository Qualification Engine; others shift |
| **Free-Tier Stack** | ✅ Unchanged | Groq, OpenRouter, Supabase, GitHub Actions |

### What Changes

| From v4 | To v4.2 | Reason |
|---------|---------|--------|
| Curated `repos.yaml` | GitHub Search API discovery + heuristic scoring | Product differentiator |
| Static repo list | Dynamic repo qualification with Contribution Success Score 0-100 | Demonstrates systems thinking |
| Pipeline starts at "Scan issues" | Pipeline starts at "Discover repos" | Mentor, not explainer |
| Sprint 2: GitHub Client | Sprint 2: GitHub Client + Discovery | Foundation for qualification |
| Sprint 3: Repo Management | Sprint 3: Repository Qualification Engine (★) | The differentiator sprint |
| Sprint 4: Code Indexing | Sprint 4: Repo Ranking + API | Show scores via API early |
| Sprint 5: RAG Retrieval | Sprint 5: Code Indexing | Shifted down |
| Sprint 6: LLM | Sprint 6: RAG Retrieval | Shifted down |
| Sprint 7: Classify | Sprint 7: LLM Mentor | Shifted down |

---

## Summary: The One Change That Matters

**Before v4.1:** GitNova was a RAG-powered issue explainer with a curated repo list.

**After v4.2:** GitNova helps developers **find their first successful open-source contribution with confidence** — using a Repository Qualification Engine that produces a transparent Contribution Success Score, RAG-grounded LLM mentoring, and production-grade Python engineering.

The Repository Qualification Engine is:
- **Explainable** — every point is defensible
- **Zero-cost** — no ML training, no GPU
- **Differentiated** — no competitor does this
- **Interview-proof** — you can whiteboard the entire scoring logic

### Final Validation Checklist

Before finalizing any modification, ask:

1. Does this improve the probability of a beginner making a successful, merged contribution?
2. Does this make GitNova more memorable than a generic RAG application?
3. Can the developer explain every architectural decision in an AI Engineer interview?
4. Is this still realistic for one developer using free-tier services?

If the answer to any question is "No", revise the design.

Preserve engineering excellence. Strengthen product thinking. Do not increase unnecessary complexity.

---

*End of v4.2 Product Vision Shift Document*
