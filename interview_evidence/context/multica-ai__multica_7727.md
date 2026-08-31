# Issue Context Dossier: `multica-ai/multica` #7727

**Title:** Tasks for agents owned by a different user than the runtime owner are silently stuck in `queued` forever (no error anywhere)  
**Repository:** https://github.com/multica-ai/multica  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Tasks assigned to agents whose owner does not match the daemon's runtime owner get silently stuck in the queued state forever because SQL query filters exclude them when agent owner ID and runtime owner ID diverge on private runtimes, resulting in silent drops with no user-facing errors or daemon logs.

## 2. Root Cause Analysis
> The database query `ListQueuedClaimCandidatesByRuntime` filters out claim candidates using an authorization fence where private runtimes require `r.owner_id = a.owner_id`. When owners differ, no candidates match, causing the daemon to receive an empty claim set and silently drop execution without logging a rejection reason.

## 3. Grounded Code Locations & Citations
- File: `server/internal/attribution/attribution.go` (Lines: `1-40`) | Symbol: `TriggerKind` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect attribution query and runtime owner authorization check**: Inspect server/internal/attribution/attribution.go around the database query ListQueuedClaimCandidatesByRuntime to understand how agent and runtime owner IDs are filtered and where tasks are silently dropped. (Target: `server/internal/attribution/attribution.go`)
2. **Implement fail-fast error handling for owner mismatch**: Update the task claim and attribution workflow in server/internal/attribution/attribution.go to detect when an agent's owner does not match the private runtime's owner, explicitly marking the task with an authorization error rather than silently leaving it queued. (Target: `server/internal/attribution/attribution.go`)
3. **Add regression test for owner mismatch behavior**: Add a new test case in server/internal/attribution/attribution_test.go or server/internal/attribution/delegated_subscriber_test.go that sets up an agent and private runtime with mismatched owner IDs and asserts that the task fails fast with the expected error message. (Target: `server/internal/attribution/attribution_test.go`)
4. **Run unit and integration test suite**: Execute the verified test command to verify that all attribution and delegation tests pass successfully without regressions. (Target: `None`)

## 5. Educational Concepts
### Authorization Fences in Database Queries
- **What is it:** A security or access-control check implemented directly inside a SQL query using conditions (like WHERE clauses) to restrict which rows can be accessed or claimed by a specific user or runtime.
- **Why it matters:** Developers need to understand that if data fails an authorization fence in a query, it is simply omitted from result sets rather than throwing an explicit database error, which can cause operations to quietly stall.
- **Connection to Issue:** The query ListQueuedClaimCandidatesByRuntime uses an ownership condition that silently filters out tasks when an agent's owner does not match the private runtime's owner.

### Silent Failure vs. Explicit Error Handling
- **What is it:** The anti-pattern of discarding work or ignoring conditions without emitting logs, error states, or user-facing feedback when an invalid state or authorization mismatch occurs.
- **Why it matters:** Silent failures leave developers and users completely blind to why a system is not working, masking configuration or permission mismatches as mysterious bugs.
- **Connection to Issue:** Mismatched agent and runtime owners cause tasks to be dropped or ignored by the daemon without recording any rejection reason or terminal task error.

