# Issue Context Dossier: `nexu-io/open-design` #7581

**Title:** [Bug]: Win11 无法安装  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> On Windows platforms, when installing OpenDesign or staging packaged resources, absolute paths or space-containing paths in Windows can cause setup scripts or command execution steps to fail when passing unescaped or split paths to underlying helper tools or package managers.

## 2. Root Cause Analysis
> Path resolution in `stageVerifiedBundleInProfile` or subprocess environment creation can pass absolute paths containing spaces to Windows shell or package manager execution utilities without proper quoting or by using unescaped absolute paths instead of safe relative specifications.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/agent-companion-setup.ts` (Lines: `141-180`) | Symbol: `stageVerifiedBundleInProfile` | Role: *Handles staging bundle files in profile directories and managing relative paths on Windows.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect staging control flow**: Inspect stageVerifiedBundleInProfile in apps/daemon/src/agent-companion-setup.ts to locate where absolute packaged app paths or bundle files are passed to subprocess or file staging utilities. (Target: `apps/daemon/src/agent-companion-setup.ts`)
2. **Ensure safe quoting and path handling**: Update path resolution and command execution parameters within stageVerifiedBundleInProfile to properly quote or handle absolute paths containing spaces on Windows platforms. (Target: `apps/daemon/src/agent-companion-setup.ts`)
3. **Add regression test for paths with spaces**: Add a unit or integration test simulating Windows absolute paths with spaces (e.g. containing 'OpenDesign') to verify that stageVerifiedBundleInProfile correctly stages bundles without path-splitting or command execution failures. (Target: `apps/daemon/src/agent-companion-setup.ts`)
4. **Run test suite verification**: Run the repository test suite to confirm that all tests pass successfully with the updated path handling logic. (Target: `None`)

## 5. Educational Concepts
### Windows Path Handling and Spaces
- **What is it:** Operating systems like Windows often use spaces in directory names (e.g. 'Program Files' or custom app folders), which can break command-line arguments if spaces are interpreted as argument separators.
- **Why it matters:** Developers must ensure that file paths passed to child processes or shells are properly quoted or kept relative to avoid command parsing failures.
- **Connection to Issue:** The comment in `stageVerifiedBundleInProfile` explicitly notes that keeping specs relative avoids Windows shell forwarder splitting absolute paths at spaces.

### Subprocess Invocation and Shell Quoting
- **What is it:** Executing external commands via Node.js `child_process` requires careful handling of arguments, environment variables, and command options (like `windowsVerbatimArguments`).
- **Why it matters:** Incorrect argument formatting leads to unexpected command termination or syntax errors during app installation.
- **Connection to Issue:** Fixing installation issues on Windows involves ensuring package manager and script invocations correctly handle paths with spaces.

