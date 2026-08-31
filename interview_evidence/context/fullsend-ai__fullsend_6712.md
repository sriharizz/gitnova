# Issue Context Dossier: `fullsend-ai/fullsend` #6712

**Title:** Scribe: auto-apply ready-for-triage label on created issues  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Scribe creates new GitHub issues as part of its agent role, but the issues currently lack the mandatory `ready-for-triage` label, requiring manual intervention to enter the triage pipeline. This issue requires updating Scribe's issue creation logic to automatically apply the `ready-for-triage` label using Scribe's own GitHub App identity.

## 2. Root Cause Analysis
> Scribe's issue creation routine currently invokes GitHub API calls to create issues without including the `ready-for-triage` label argument or configuration in the creation request payload, and needs to be extended to supply this label.

## 3. Grounded Code Locations & Citations
- File: `internal/dispatch/router.go` (Lines: `106-145`) | Symbol: `routeLabel` | Role: *Relevant Code* (Verified: True)
- File: `internal/config/config.go` (Lines: `141-180`) | Symbol: `DispatchConfig` | Role: *Relevant Code* (Verified: True)
- File: `internal/appsetup/appsetup.go` (Lines: `106-145`) | Symbol: `Setup` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect routeLabel and dispatch configuration**: Inspect symbol routeLabel in internal/dispatch/router.go and DispatchConfig in internal/config/config.go to understand how labels and issues are currently handled during dispatch and creation. (Target: `internal/dispatch/router.go`)
2. **Update issue creation payload to include ready-for-triage**: Modify the issue creation routine to automatically append the 'ready-for-triage' label in the creation request payload using Scribe's GitHub App identity. (Target: `internal/dispatch/router.go`)
3. **Write regression test for automatic label application**: Add a unit test in internal/dispatch/router_test.go verifying that newly created issues include the mandatory 'ready-for-triage' label in their creation parameters. (Target: `internal/dispatch/router_test.go`)
4. **Run test suite for verification**: Execute the package tests to ensure the new label is correctly applied and no existing routing or issue creation behavior is broken. (Target: `None`)

## 5. Educational Concepts
### GitHub App Identity and Authentication
- **What is it:** A mechanism allowing automated bots or agents to act with their own dedicated installation token and permissions rather than relying on human or generic tokens.
- **Why it matters:** Using dedicated app identities ensures proper audit trails, granular permission scoping, and prevents permission escalation bugs.
- **Connection to Issue:** Scribe must apply the `ready-for-triage` label using its own newly minted `scribe` app identity instead of the triage agent's permissions.

### Automated Issue Triage Pipelines
- **What is it:** Workflows triggered by specific labels or event states that automate the distribution and handling of incoming work items.
- **Why it matters:** Properly labeling newly created issues ensures they instantly route into the correct automated queue without manual operator intervention.
- **Connection to Issue:** Applying the `ready-for-triage` label automatically upon Scribe issue creation allows the triage pipeline to immediately process the issue.

