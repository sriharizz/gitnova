# Issue Context Dossier: `fullsend-ai/fullsend` #5967

**Title:** Filter pull_request_review events in fullsend.yaml shim to changes_requested state  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The fullsend.yaml GitHub Actions shim workflow forwards all pull_request_review: types: [submitted] events to the dispatch workflow regardless of review state. This causes a high volume of redundant no-op runs when humans leave inline comments or reviews with states other than 'changes_requested'. This issue proposes filtering pull_request_review events at the workflow shim level so that only reviews with state 'changes_requested' trigger the fullsend.yaml shim run.

## 2. Root Cause Analysis
> The GitHub Actions workflow template (.github/workflows/fullsend.yaml or scaffold template) listens broadly to `pull_request_review: types: [submitted]` without an event-state filter condition, causing GitHub to queue and dispatch jobs for every review submission regardless of its state.

## 3. Grounded Code Locations & Citations
- File: `internal/dispatch/router.go` (Lines: `1-40`) | Symbol: `HarnessRouter.Route` | Role: *Relevant Code* (Verified: True)
- File: `internal/harnessdispatch/auth.go` (Lines: `1-37`) | Symbol: `IsAuthorized` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect HarnessRouter and Event Routing Control Flow**: Examine HarnessRouter.Route in internal/dispatch/router.go and IsAuthorized in internal/harnessdispatch/auth.go to understand how pull_request_review events and their review states are evaluated. (Target: `internal/dispatch/router.go`)
2. **Locate Workflow Shim Event Trigger Configuration**: Locate the fullsend.yaml GitHub Actions workflow file or template where pull_request_review triggers are defined under the types: [submitted] filter. (Target: `.github/workflows/fullsend.yaml`)
3. **Add Conditional Event Filtering for Review States**: Update the workflow trigger configuration or router check to ensure that only pull_request_review events with state 'changes_requested' proceed, avoiding redundant no-op runs. (Target: `.github/workflows/fullsend.yaml`)
4. **Add Regression Test Coverage**: Update router_test.go or auth_test.go in internal/dispatch/ and internal/harnessdispatch/ to assert that review payloads with states other than 'changes_requested' are correctly ignored or filtered out. (Target: `internal/dispatch/router_test.go`)
5. **Run Test Suite for Verification**: Execute the package test suite using the standard Go test command to verify that all existing and new routing tests pass successfully. (Target: `internal/dispatch/router_test.go`)

## 5. Educational Concepts
### Workflow Event Filtering in GitHub Actions
- **What is it:** Using job `if` conditional guards in workflow YAML files to filter events before jobs are allocated runner resources.
- **Why it matters:** Preventing unnecessary workflow runs saves CI compute minutes, avoids pending-queue limits, and reduces noise in build logs.
- **Connection to Issue:** Adding a review state filter condition to the workflow shim prevents non-actionable review states like 'COMMENTED' or 'APPROVED' from spawning costly no-op runner jobs.

### Event Normalization and Routing
- **What is it:** The architectural separation between coarse-grained workflow trigger shims and fine-grained event routing/authorization logic.
- **Why it matters:** Keeping coarse filters at the CI trigger level prevents wasted orchestration overhead while backend routing logic handles precise business rules.
- **Connection to Issue:** While the backend router correctly ignores non-changes_requested reviews, filtering them earlier at the GitHub Actions workflow shim level prevents unnecessary runner job startups.

