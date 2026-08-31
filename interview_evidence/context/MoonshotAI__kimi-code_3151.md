# Issue Context Dossier: `MoonshotAI/kimi-code` #3151

**Title:** [Bug] Windows: sessions imported by kimi migrate invisible in /sessions picker (workDir slash mismatch)  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> On Windows, legacy sessions migrated from kimi-cli record working directories using Windows backslashes (e.g. 'D:\code\edcbook') in the session index. Meanwhile, native Windows kimi-code 0.38.0 sessions record forward slashes ('D:/code\edcbook' or 'D:/code/edcbook'). Because the session picker filters index entries by an exact string match against the current working directory, migrated sessions remain completely invisible in the UI picker.

## 2. Root Cause Analysis
> Migration imports legacy session metadata containing backslash directory paths into `session_index.jsonl` without normalizing them to the forward-slash canonical form used by the native build. The session lookup or filtering logic performs a strict string comparison against the current process cwd, creating a mismatch.

## 3. Grounded Code Locations & Citations
- File: `apps/vscode/src/extension.ts` (Lines: `211-250`) | Symbol: `performMigration` | Role: *Legacy migration execution handler* (Verified: True)
- File: `packages/acp-server/src/server.ts` (Lines: `316-355`) | Symbol: `listSessions` | Role: *Session listing and filtering logic* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect session listing and migration handling**: Inspect the performMigration function in apps/vscode/src/extension.ts and listSessions in packages/acp-server/src/server.ts to understand how working directory paths are recorded and filtered. (Target: `apps/vscode/src/extension.ts`)
2. **Normalize paths during migration**: Update performMigration in apps/vscode/src/extension.ts to normalize legacy session working directory paths to use consistent forward slashes or platform-agnostic formatting before saving them. (Target: `apps/vscode/src/extension.ts`)
3. **Implement robust path comparison in session filtering**: Modify listSessions in packages/acp-server/src/server.ts to normalize both index working directories and the current working directory (handling backslashes and case sensitivity on Windows) during filtering. (Target: `packages/acp-server/src/server.ts`)
4. **Write regression tests and verify via test command**: Add unit tests verifying that migrated sessions with backslashes correctly match and appear in session listings on Windows, then run the test suite using pnpm test. (Target: `packages/acp-server/src/server.ts`)

## 5. Educational Concepts
### Path Normalization
- **What is it:** Converting file paths into a standard, canonical string format (e.g., standardizing path separators and casing).
- **Why it matters:** Different operating systems represent paths differently, and naive string comparisons fail when path separators or drive letter casing vary.
- **Connection to Issue:** Migrated sessions contain backslashes while native sessions use forward slashes, causing exact-match filtering to fail until paths are normalized.

### Session Indexing and Filtering
- **What is it:** Maintaining a persistent registry or index of user sessions to quickly locate and load conversation history.
- **Why it matters:** Allows users to filter and view past chats associated with a specific working directory.
- **Connection to Issue:** The session picker relies on matching the stored session working directory against the current process working directory.

