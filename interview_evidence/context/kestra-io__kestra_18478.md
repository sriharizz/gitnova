# Issue Context Dossier: `kestra-io/kestra` #18478

**Title:** [Bash2.0] Concurrency limit running count accepts negative values and disables the limit  
**Repository:** https://github.com/kestra-io/kestra  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The concurrency-limit editor endpoint currently allows setting any running count value, including negative numbers and numbers exceeding capacity, which can silently turn concurrency limits off or queue executions forever. Additionally, requests can bypass intended path validation parameters.

## 2. Root Cause Analysis
> The endpoint handlers lack strict input validation checks for the concurrency running count (permitting negative values) and fail to validate that the path-scoped namespace and flowId match the payload content.

## 3. Grounded Code Locations & Citations
- File: `executor/src/main/java/io/kestra/executor/ExecutorService.java` (Lines: `106-145`) | Symbol: `io.kestra.executor.ExecutorService` | Role: *Relevant Code* (Verified: True)
- File: `executor/src/main/java/io/kestra/executor/ConcurrencySlotReleaseProcessor.java` (Lines: `36-75`) | Symbol: `io.kestra.executor.ConcurrencySlotReleaseProcessor` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect concurrency limit endpoint handler and validation logic**: Inspect symbol ExecutorService in file executor/src/main/java/io/kestra/executor/ExecutorService.java and verify where running counts and path parameters are processed without validation. (Target: `executor/src/main/java/io/kestra/executor/ExecutorService.java`)
2. **Add validation for non-negative running counts**: Update the concurrency limit update logic in ExecutorService to reject negative running count values or values exceeding valid limits. (Target: `executor/src/main/java/io/kestra/executor/ExecutorService.java`)
3. **Enforce path parameter matching against request body**: Validate that the namespace and flowId provided in the request path match the payload content in ExecutorService before persisting or applying state changes. (Target: `executor/src/main/java/io/kestra/executor/ExecutorService.java`)
4. **Write regression tests for concurrency limit validation**: Add regression tests covering negative running counts and mismatched path parameters to ensure appropriate error responses or rejections are returned. (Target: `executor/src/main/java/io/kestra/executor/ConcurrencyLimitStateStore.java`)

## 5. Educational Concepts
### Input Validation & Boundary Checking
- **What is it:** Ensures that data received from external API requests falls within expected, safe logical bounds before processing.
- **Why it matters:** Without proper bounds checking, malformed or malicious inputs (like negative counters) can corrupt internal state or bypass system safeguards.
- **Connection to Issue:** Fixes the bug by rejecting negative running counts that disable flow concurrency limits.

### Path-to-Payload Parameter Binding
- **What is it:** Verifies that path variables in REST endpoints (namespace, flowId) match the resource identifiers specified in the request body.
- **Why it matters:** Prevents unauthorized or accidental updates to unintended resources across different namespaces.
- **Connection to Issue:** Ensures requests targeted at a specific flow path cannot inadvertently modify another flow's concurrency state.

