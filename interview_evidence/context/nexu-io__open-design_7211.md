# Issue Context Dossier: `nexu-io/open-design` #7211

**Title:** [Bug]: Windows CLI (Antigravity) is not normal...  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The user reports an issue on Windows where the local CLI (Antigravity) and the Antigravity app version exhibit abnormal chat continuity behavior, frequently restarting conversations with standard greetings instead of continuing the history.

## 2. Root Cause Analysis
> On Windows, subprocesses spawned by the daemon can encounter environment mismatches—specifically with credential stores, WSL/PowerShell vs. native Windows environments, or config directory lookups—triggering authentication fallbacks or session state invalidations that restart conversations.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/claude-diagnostics.ts` (Lines: `190-210`) | Symbol: `windowsCredentialMismatch` | Role: *Detects Windows-specific credential manager, PowerShell, and WSL environment mismatches during agent execution* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect windowsCredentialMismatch symbol**: Inspect the windowsCredentialMismatch function within apps/daemon/src/claude-diagnostics.ts to understand how Windows credential manager mismatches and shell path variations are currently evaluated. (Target: `apps/daemon/src/claude-diagnostics.ts`)
2. **Refine Environment Handling for Subprocesses**: Update the environment propagation logic in apps/daemon/src/claude-diagnostics.ts to correctly preserve Windows credential store paths and prevent session state invalidations. (Target: `apps/daemon/src/claude-diagnostics.ts`)
3. **Implement Regression Test in Connection Test Suite**: Add a new test case within apps/daemon/src/connectionTest.ts to simulate Windows environment discrepancies and verify that conversation continuity and session credentials persist across subprocess turns. (Target: `apps/daemon/src/connectionTest.ts`)
4. **Run Verification Test Command**: Execute the test suite to validate that the credential and environment mismatch fixes prevent premature chat resets on Windows. (Target: `None`)

## 5. Educational Concepts
### Environment Isolation and Subprocess Spawning
- **What is it:** How parent applications spawn child processes and pass down environment variables and configuration contexts.
- **Why it matters:** If environment variables or credential manager paths differ between the host shell and spawned child processes, external agent CLIs will fail to authenticate or access state.
- **Connection to Issue:** On Windows, differences between native Windows, PowerShell, and WSL environments cause credential mismatches that break CLI conversation continuity.

### Diagnostic Error Mapping
- **What is it:** Translating raw CLI and process error output into actionable user-facing troubleshooting advice.
- **Why it matters:** Clear diagnostics guide users to resolve local environment or authentication discrepancies quickly.
- **Connection to Issue:** Helps detect when Windows credential manager or profile configuration issues occur and instructs users on proper re-authentication.

