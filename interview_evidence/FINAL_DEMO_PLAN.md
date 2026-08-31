# GitNova — Live Technical Interview Demo Plan

Use this exact 3-issue demonstration hierarchy during your technical interview.

---

## 1. Primary Demo Issue: `pallets/click #2645` (Python — Unit Test Coverage)
- **Why Selected:** It is crisp, beginner-friendly, and has 100% AST-verified grounding in a world-renowned Python library (`click`).
- **What Screens to Show:**
  1. **Feed View:** Show the card with `Python`, `BEGINNER` badge, and `92/100` score.
  2. **Stage 01 (Understand):** Show plain-English summary of adding test coverage for float/int parameter coercion error messages.
  3. **Stage 04 (Code Explorer):** Show verified citation for `tests/test_types.py` (Lines 112–145).
  4. **Stage 08 (Test):** Show exact pytest regression command (`pytest -k test_types`).
- **Interviewer Questions & Defense:**
  - *Q: "How did GitNova know which test file to touch?"*
  - *A: "Our hybrid retriever fused dense semantic embeddings of parameter coercion with sparse keyword matches for `IntParamType` to isolate `tests/test_types.py`."*

---

## 2. Backup Technical Issue: `deepset-ai/haystack #10721` (Python — Architecture & Type Systems)
- **Why Selected:** Demonstrates deep architectural intelligence on a modern AI/LLM orchestration framework (`haystack`).
- **What Screens to Show:**
  1. **Stage 03 (Learn Concepts):** Expand concept cards on *Variadic Type Annotations (`Variadic[Document]`)* and *Pipeline Socket Multiplexing*.
  2. **Stage 05 (Investigate):** Show root cause control-flow analysis explaining why connecting multiple document outputs to `PromptBuilder.documents` raises a typing conflict.
  3. **Stage 06 (Plan Fix):** Show 4-step minimal change plan modifying type validation in `src/haystack/components/builders/prompt_builder.py`.
- **Interviewer Questions & Defense:**
  - *Q: "Why is this not classified as a pure beginner issue?"*
  - *A: "Because modifying type hints in pipeline sockets requires understanding framework internals; GitNova accurately classified it as an intermediate architectural bug."*

---

## 3. Optional Deep Technical Issue: `paradedb/paradedb #6104` (Rust — Database Engine Numeric Typmod Bug)
- **Why Selected:** Demonstrates multi-language capability and systems-level database indexing intelligence (PostgreSQL + Rust).
- **What Screens to Show:**
  1. **Stage 01 (Understand):** Show range-partitioned join scan numeric bound conversion bug.
  2. **Stage 04 (Code Explorer):** Show verified citations in `packages/ParadeDB/join.rs`.
  3. **Stage 08 (Test):** Show `cargo test` command.
- **Interviewer Questions & Defense:**
  - *Q: "Does GitNova support compiled languages like Rust?"*
  - *A: "Yes. Our Tree-sitter parser extracts Rust struct definitions and impl blocks with equal fidelity to Python ASTs."*
