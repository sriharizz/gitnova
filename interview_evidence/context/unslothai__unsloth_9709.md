# Issue Context Dossier: `unslothai/unsloth` #9709

**Title:** [Studio 0.1.803-beta] web_search can be called with empty arguments and returns "No query provided"  
**Repository:** https://github.com/unslothai/unsloth  
**Language:** Python  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> In Unsloth Studio/Desktop, the built-in web_search tool can be invoked by local models with an empty argument object ({}), resulting in a 'No query provided' error that stalls or breaks agent execution turns.

## 2. Root Cause Analysis
> The underlying tool schema defines `query` and `url` as optional properties with `required: []`. At execution time, the arguments dictionary is unpacked without verifying whether both `query` and `url` evaluate to empty/whitespace strings, allowing invalid empty calls to pass through to the execution backend.

## 3. Grounded Code Locations & Citations
- File: `studio/backend/core/research_runs.py` (Lines: `724-732`) | Symbol: `_research_step_failed` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect web_search tool execution handling**: Inspect studio/backend/core/research_runs.py to locate where the web_search tool parses its arguments and executes the search query. (Target: `studio/backend/core/research_runs.py`)
2. **Add validation for empty query and url arguments**: Modify the web_search tool execution block in studio/backend/core/research_runs.py to check if both query and url are empty, missing, or whitespace-only before proceeding. (Target: `studio/backend/core/research_runs.py`)
3. **Return a recoverable model-visible error message**: Ensure that when empty arguments ({}) are provided, the tool returns a clear, recoverable error message back to the model prompting it to supply a valid query or url instead of failing silently or breaking execution. (Target: `studio/backend/core/research_runs.py`)
4. **Add regression test and verify execution**: Add a unit or integration test simulating a model call with empty arguments ({}) to the web_search tool and assert that a proper recoverable error is returned. (Target: `studio/backend/core/research_runs.py`)

## 5. Educational Concepts
### Tool Argument Validation & Defensive Input Checking
- **What is it:** Validating input parameters received from LLM tool calls before executing backend logic.
- **Why it matters:** LLMs can occasionally output malformed, empty, or unexpected tool arguments. Proper validation prevents runtime crashes and allows returning informative error messages so the model can self-correct.
- **Connection to Issue:** Adding an execution-time check to verify that neither `query` nor `url` are empty or whitespace-only prevents passing invalid arguments into the search backend.

### JSON Schema Required Fields
- **What is it:** Using JSON schema definitions to specify which parameters are mandatory for a tool or function call.
- **Why it matters:** Enforcing schema requirements guides the LLM on what inputs must be generated for a successful tool invocation.
- **Connection to Issue:** The issue stems from `required: []` allowing empty arguments; understanding tool schemas helps structure robust alternative validation or schema constraints.

