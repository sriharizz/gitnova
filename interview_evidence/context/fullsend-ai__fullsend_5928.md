# Issue Context Dossier: `fullsend-ai/fullsend` #5928

**Title:** Post-script should submit formal COMMENT review when it minimizes a prior APPROVED review in the same run  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The post-review script/harness incorrectly skips submitting a formal COMMENT review when a prior APPROVED review is minimized in the same run, leaving the pull request with zero visible formal reviews.

## 2. Root Cause Analysis
> The skip-COMMENT optimization condition checks whether a sticky comment was updated but fails to verify whether any prior formal review was minimized during the same run, causing the PR review state to transition from approved to zero visible reviews.

## 3. Grounded Code Locations & Citations
- File: `internal/dispatch/router.go` (Lines: `36-75`) | Symbol: `HarnessRouter.routeComment` | Role: *Relevant Code* (Verified: True)
- File: `internal/harnessdispatch/auth.go` (Lines: `1-37`) | Symbol: `IsAuthorized` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect HarnessRouter.routeComment Control Flow**: Inspect symbol HarnessRouter.routeComment in internal/dispatch/router.go to understand the skip-COMMENT optimization logic when prior reviews are minimized. (Target: `internal/dispatch/router.go`)
2. **Update Skip-COMMENT Condition**: Modify the condition in internal/dispatch/router.go to ensure that if a prior formal review is minimized during the run, the script bypasses the skip-COMMENT optimization and submits a formal COMMENT review. (Target: `internal/dispatch/router.go`)
3. **Add Regression Test in router_test.go**: Add a new unit test in internal/dispatch/router_test.go validating that a comment verdict accompanied by a minimized prior formal review successfully submits a formal COMMENT review. (Target: `internal/dispatch/router_test.go`)
4. **Run Test Suite**: Run the test suite using go test ./internal/dispatch/... to verify the fix and ensure no regressions are introduced. (Target: `internal/dispatch/router_test.go`)

## 5. Educational Concepts
### Review State Minimization and Visibility
- **What is it:** GitHub allows multiple reviews on a pull request, but older reviews can be minimized or marked as outdated when new reviews are submitted.
- **Why it matters:** Developers and automated systems rely on visible review badges (Approved, Changes Requested, Commented) to determine whether a pull request is ready to merge.
- **Connection to Issue:** When an older APPROVED review is minimized and no new formal COMMENT review is posted because of incorrect skip logic, the PR ends up with zero visible reviews.

### Conditional Execution Flags in Automation Scripts
- **What is it:** Boolean optimization flags that bypass certain steps if other states are satisfied.
- **Why it matters:** Incorrectly scoped bypass conditions can inadvertently skip critical side-effects under edge-case combinations of states.
- **Connection to Issue:** The skip-COMMENT optimization logic assumes that updating a sticky comment replaces the need for a formal review, failing to account for concurrent review minimization.

