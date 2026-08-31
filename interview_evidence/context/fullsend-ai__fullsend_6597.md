# Issue Context Dossier: `fullsend-ai/fullsend` #6597

**Title:** Shim version drift blocks review dispatch for bot-authored PRs on ci-failure-tracker  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Bot-authored PRs fail review dispatch because target repository shims are outdated (pinned to v0.30.0), lacking the 'labeled' trigger type needed to route ready-for-review events around permission limitations.

## 2. Root Cause Analysis
> The repository's shim workflow is pinned to an older version (v0.30.0) whose `on.pull_request_target.types` omits `labeled` and lacks the route handler for `pull_request_target/labeled` events, which were introduced in subsequent versions to bypass bot collaborator permission API limitations.

## 3. Grounded Code Locations & Citations
- File: `internal/dispatch/router.go` (Lines: `1-40`) | Symbol: `HarnessRouter` | Role: *Event routing and stage mapping* (Verified: True)
- File: `internal/harnessdispatch/auth.go` (Lines: `1-37`) | Symbol: `IsAuthorized` | Role: *Authorization gate for dispatch events* (Verified: True)
- File: `internal/config/config.go` (Lines: `1-40`) | Symbol: `DefaultGHRunner` | Role: *Configuration defaults and runner settings* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Event Router Control Flow**: Inspect symbol HarnessRouter in internal/dispatch/router.go and verify how pull_request_target events and stage matching are structured. (Target: `internal/dispatch/router.go`)
2. **Inspect Authorization Gate**: Inspect symbol IsAuthorized in internal/harnessdispatch/auth.go to understand how bot collaborator permissions and authorization gates are evaluated during dispatch. (Target: `internal/harnessdispatch/auth.go`)
3. **Update Shim Workflow Triggers**: Update the repository shim workflow configuration in .github/workflows/fullsend.yaml to include the 'labeled' trigger type for pull_request_target events. (Target: `.github/workflows/fullsend.yaml`)
4. **Add Regression Test Cases**: Add regression test cases in internal/dispatch/router_test.go and internal/harnessdispatch/auth_test.go to verify correct routing and authorization for pull_request_target/labeled events. (Target: `internal/dispatch/router_test.go`)
5. **Run Test Suite**: Run the test suite using go test to confirm that the changes pass successfully and fix the review dispatch issue for bot-authored PRs. (Target: `None`)

## 5. Educational Concepts
### GitHub Actions Event Triggers
- **What is it:** The specific event types and activities (like pull_request_target with opened, synchronize, or labeled) that tell GitHub when to run a workflow file.
- **Why it matters:** If a workflow trigger type is missing from the YAML file, GitHub Actions will never fire the workflow for that specific event, preventing downstream routing logic from ever executing.
- **Connection to Issue:** The outdated shim lacks the 'labeled' trigger type under pull_request_target, preventing ready-for-review label events from triggering the workflow.

### Bot Authorization & Collaborator Permissions
- **What is it:** Security checks that verify whether an event actor has sufficient repository permissions to trigger automated actions.
- **Why it matters:** Bot accounts often lack standard write permissions in the collaborator API, requiring alternative routing paths (like label-added events) to authorize securely.
- **Connection to Issue:** Bot-authored PRs fail the standard opened check because bots lack write-level collaborator access, necessitating the labeled event bypass.

