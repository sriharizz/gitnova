# GitNova — Live Technical Interview Demo Runbook

Follow this step-by-step click and presentation script during your interview tomorrow:

---

### Step 1: Open the Application & Pitch (1 Minute)
- **URL**: `https://gitnovav2.vercel.app/issues`
- **What to say**: *"GitNova is an autonomous developer intelligence platform that transforms raw GitHub issues into structured, 10-stage guided contribution journeys. It solves the Good First Issue crisis by filtering out 91.8% of noise and providing repository-grounded technical guidance."*

---

### Step 2: Show Dynamic Preference Filtering (1 Minute)
- **Click**: Click on **"Beginner"** tier pill, or click **"Customize Stack"** and select `Python` and `TypeScript`.
- **What to say**: *"The feed dynamically personalizes opportunities based on tech stack, domain topics, and verified beginner suitability. Notice every card displays an AST verification badge and a 0-100 suitability score."*

---

### Step 3: Open a Live Demo Issue (2 Minutes)
- **Click**: Click **"Start"** on `deepset-ai/haystack #10721` or `pallets/click #2645`.
- **Demonstrate the 10 Stages**:
  1. **Stage 1 (Understand)**: Point out the plain-English summary.
  2. **Stage 3 (Learn Concepts)**: Expand concept cards (*Variadic Type Annotations*).
  3. **Stage 4 (Explore Code)**: Show verified file path citations (`src/haystack/pipeline.py`).
  4. **Stage 5 (Investigate)**: Show root cause control-flow analysis.
  5. **Stage 6 (Plan Fix)**: Show step-by-step minimal change plan.
  6. **Stage 8 (Test)**: Show exact pytest regression command.

---

### Step 4: Explain the Data Science & ML Behind It (2 Minutes)
- **What to say**:
  - *"We evaluated our RAG retrieval against historical merged PRs, achieving 94% Recall@1 and 100% Recall@5."*
  - *"We also conducted an offline QLoRA fine-tuning experiment on 600 issues across 73 repos using a strict repository-held-out split, lifting Macro-F1 from 20.96% (zero-shot) to 79.41%."*
