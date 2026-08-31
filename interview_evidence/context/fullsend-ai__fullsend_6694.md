# Issue Context Dossier: `fullsend-ai/fullsend` #6694

**Title:** Suppress or fix LoadWithBase dispatch error for repos using harness base composition  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> On PR dispatches for repositories using harness base composition (such as a base field in review.yaml pointing to a remote template), the fullsend harness dispatch logs an error stating that the harness was not loaded with LoadWithBase. Even though the review agent falls back and executes successfully, this creates persistent log noise during PR runs.

## 2. Root Cause Analysis
> The CLI dispatch command code path that loads harness configurations for agent routing fails to use the `LoadWithBase` function required when a harness config specifies a `base:` field for composition.

## 3. Grounded Code Locations & Citations
- File: `internal/harnessdispatch/core.go` (Lines: `1-40`) | Symbol: `Dispatch` | Role: *Relevant Code* (Verified: True)
- File: `internal/config/config.go` (Lines: `281-320`) | Symbol: `ValidAgentNames` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Harness Dispatch Loading Logic**: Inspect symbol Dispatch in internal/harnessdispatch/core.go to locate where harness configurations are initially loaded before agent execution. (Target: `internal/harnessdispatch/core.go`)
2. **Update Configuration Loading to Support Base Composition**: Modify the harness loading routine in internal/harnessdispatch/core.go to utilize LoadWithBase (or equivalent base composition support) instead of standard loading when a base configuration field is present. (Target: `internal/harnessdispatch/core.go`)
3. **Add or Update Regression Test in core_test.go**: Add a test case in internal/harnessdispatch/core_test.go simulating a harness configuration using a remote or local base field, asserting that dispatch loads successfully without triggering base composition log errors. (Target: `internal/harnessdispatch/core_test.go`)
4. **Run Test Suite**: Execute the package test suite to verify that the harness dispatch fix resolves the log noise and does not break existing agent execution paths. (Target: `internal/harnessdispatch/core_test.go`)

## 5. Educational Concepts
### Harness Base Composition
- **What is it:** A feature allowing configuration files (harnesses) to inherit from or compose with a base configuration template.
- **Why it matters:** Enables modular reuse of agent configurations across repositories without duplicating common workflow settings.
- **Connection to Issue:** Repos utilizing this composition feature trigger an error during dispatch because the loading mechanism expects a specialized load function (`LoadWithBase`).

### Error vs. Debug Log Levels
- **What is it:** Categorizing runtime messages by severity to prevent unnecessary alarms for non-fatal fallback paths.
- **Why it matters:** Proper log levels ensure that real failures stand out and are not obscured by routine fallback warnings.
- **Connection to Issue:** The issue notes that since the review agent still executes successfully via fallback, logging at error level creates unnecessary noise that could mask genuine issues.

