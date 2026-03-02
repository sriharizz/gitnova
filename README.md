# GitNova 🚀

> **Stop searching. Start contributing.**  
> An autonomous AI-powered engine that hunts for beginner-friendly Open Source issues so you don't have to.

![GitNova Banner](https://img.shields.io/badge/Status-Active-brightgreen) ![License](https://img.shields.io/badge/License-MIT-blue)

## ⚡ The Problem: Analysis Paralysis
Most developers fail at Open Source because they get stuck trying to find an issue among thousands, only to realize the issue is either too hard, lacks context, or is actually a sprawling architecture proposal. 

**GitNova** solves this by automating the hunt. It continuously scans GitHub, filters out the noise using **Hybrid Heuristics + DeBERTa v3**, and utilizes **Llama 3** to generate highly accurate, repo-grounded tactical solutions.

**🔴 Live Demo:** [gitnova-dev.vercel.app](https://gitnova-dev.vercel.app)

---

## 🏗️ The 6-Stage AI Pipeline
GitNova operates a resilient, self-correcting 6-stage data pipeline orchestrated via GitHub Actions. It processes thousands of raw issues and distills them into high-quality, actionable "Golden Nuggets".

```mermaid
flowchart LR
    A[GitHub API] --> B[Pre-Filter]
    B --> C[DeBERTa v3]
    C --> D[Repo Grounding]
    D --> E[Llama 3 Judge]
    E --> F[Post-Validator]
    F --> |Retry Loop| E
    F --> |Pass| G[Quality Scorer]
    G --> H[(Supabase)]
```

### Pipeline Architecture:
1. **GitHub API (The Hunt):** Fetches the latest open issues across 60+ top repositories (React, PyTorch, Kubernetes, etc.).
2. **Hybrid Pre-Filter:** A zero-cost rule engine that immediately drops noisy issues (RFCs, Roadmaps, all-caps rants, and markdown epic checklists).
3. **DeBERTa v3 Brain:** A zero-shot Transformer model evaluates the semantic difficulty of the issue, filtering out advanced/complex tickets.
4. **Repo Grounding (RAG):** Dynamically fetches repository metadata (language, topics, top directories) to ground the LLM prompt and prevent path hallucination.
5. **Llama 3 Agent (The Judge):** Evaluates the issue against strict heuristic prompts (banning 13+ generic SDLC verbs) to generate concrete, file-specific tactical plans.
6. **Post-Validator & Quality Scorer:** Uses regex and AST-style heuristic checks to ensure the LLM output matches the repository's file extensions and contains concrete identifiers. 
   - *Self-Correction:* If an output fails validation, the pipeline automatically feeds the failure reasons back into Llama 3 for a regeneration retry.
   - *Scoring:* Issues are ultimately graded (0-100) on Specificity, Repo Alignment, Actionability, and Hallucination Risk before being saved to Supabase.

---

## 🛠️ Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | React + Vite + Tailwind | Fast, responsive, mobile-first UI |
| **Database** | Supabase (PostgreSQL) | Stores curated issues & AI metrics |
| **NLP Engine** | HuggingFace (DeBERTa v3) | Zero-shot classification (Noise Filter) |
| **LLM Agent** | Llama 3 70B (via Groq) | Tactical plan generation & evaluation |
| **Orchestration** | Python + GitHub Actions | Automated 6-stage cron jobs |

---

## ✨ Key Features
* **🎯 AI Difficulty Scoring:** Know exactly if an issue is for Novices or Apprentices.
* **🤖 Smart Tactical Hints:** The AI tells you exactly which files to edit, which functions to look at, and what logic to change.
* **🛡️ Hallucination Defense:** Built-in validation ensures the AI doesn't suggest `.tsx` files in a Python repository.
* **📱 Mobile Ready:** Fully responsive "Card Layout" for hunting on the go.
* **🏷️ Auto-Categorization:** Issues are sorted into ML, Web Dev, DevOps, and Mobile.

---

## 🚀 Local Setup

### 1. Clone the Repo
```bash
git clone https://github.com/sriharizz/gitnova.git
cd gitnova
```

### 2. Backend Pipeline
```bash
cd backend
python -m venv env
source env/bin/activate  # Or `.\env\Scripts\activate` on Windows
pip install -r requirements.txt
```
Create a `.env` file in the `backend/` directory:
```env
GITHUB_TOKEN=your_github_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
```
Run the engine natively:
```bash
python -m app.main
```

### 3. Frontend UI
```bash
cd frontend
npm install
npm run dev
```
Create a `.env` file in the `frontend/` directory matching your Supabase credentials.

---

*GitNova — Built to cure Tutorial Hell.*
