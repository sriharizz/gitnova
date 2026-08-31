# Issue Context Dossier: `unslothai/unsloth` #9686

**Title:** studio: revisit default-on tool-call nudging, starting with the external loop  
**Repository:** https://github.com/unslothai/unsloth  
**Language:** Python  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The maintainer proposes revisiting and disabling default-on tool-call nudging specifically for the external inference loop (`studio/backend/core/inference/studio_tool_loop.py`), by updating `chat-adapter.ts` so the frontend does not send `nudge_tool_calls: true` on the external branch. Extensive measurements show that the nudge feature yields high false-positive rates, unnecessary extra generations, and corrupts conversation shapes (`user -> user` message replaying instead of `user -> assistant -> user`), whereas system-prompt guidance alone successfully handles tool calls without stateful conversation distortion.

## 2. Root Cause Analysis
> The loop-level nudge mechanism (`INTENT_SIGNAL` / `is_short_intent_without_action`) frequently fires false positives on model self-descriptions. When triggered in the external loop, it replays the stall as `user -> user`, rewriting user messages up to four times and hiding the model's previous answer.

## 3. Grounded Code Locations & Citations
- File: `studio/backend/core/research_runs.py` (Lines: `469-488`) | Symbol: `_local_model_ready` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect external inference loop and chat adapter control flow**: Examine studio/backend/core/inference/studio_tool_loop.py and locate where tool-call nudging and nudge_tool_calls parameters are parsed or handled. (Target: `studio/backend/core/inference/studio_tool_loop.py`)
2. **Disable default-on tool-call nudging on the external branch**: Modify the frontend chat-adapter configuration or external branch handler to ensure `nudge_tool_calls: true` is no longer sent by default, preventing false-positive user-to-user message replaying. (Target: `studio/backend/core/inference/studio_tool_loop.py`)
3. **Verify message sequence integrity in the inference loop**: Ensure conversation history correctly maintains `user -> assistant -> user` message shapes without corrupting prefix reuse or rewriting messages due to false-positive intent signals. (Target: `studio/backend/core/inference/studio_tool_loop.py`)
4. **Add or update regression test cases**: Update regression test scripts under studio/backend/tests/tools/capture_plan_corpus.py to verify that tool calls execute correctly without triggering unwanted nudge loops. (Target: `studio/backend/tests/tools/capture_plan_corpus.py`)
5. **Execute test suite for verification**: Run pytest on the backend tools test suite to validate that tool handling operates stably. (Target: `studio/backend/tests/tools/capture_plan_corpus.py`)

## 5. Educational Concepts
### Tool Call Nudging
- **What is it:** A loop-level retry mechanism that re-prompts a model when it outputs descriptive intent instead of executing a tool call.
- **Why it matters:** Understanding conversation loops helps prevent prompt corruption and unnecessary LLM generation calls.
- **Connection to Issue:** The issue proposes turning off default-on nudging on the external loop because measurements show it causes false positives and rewrites user messages incorrectly.

### Inference Chat Adapter State Management
- **What is it:** Frontend adapter logic that constructs request payloads (such as `nudge_tool_calls`) sent to backend endpoints.
- **Why it matters:** Properly configuring frontend parameters ensures backend loops receive expected control flags without altering core GGUF/safetensors behavior.
- **Connection to Issue:** The fix involves modifying the frontend's external branch in `chat-adapter.ts` to stop sending `nudge_tool_calls: true` by default.

