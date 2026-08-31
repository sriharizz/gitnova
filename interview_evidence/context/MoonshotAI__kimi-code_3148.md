# Issue Context Dossier: `MoonshotAI/kimi-code` #3148

**Title:** CLI 启动崩溃：ENOSPC file watchers reached（kimi / kimi -p / ACP 均复现，0.38.0）  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> CLI startup crashes with an unhandled ENOSPC error when Node.js `fs.watch` reaches the system inotify watch limit while monitoring the `~/.kimi-code` directory or configuration files.

## 2. Root Cause Analysis
> During CLI startup and initialization, the application sets up file system watchers using Node's `fs.watch` via dependencies (such as config/state watchers on `~/.kimi-code`). When the system limit for inotify watches is exhausted, Node's `fs.watch` synchronously or asynchronously throws an `ENOSPC` error which propagates unhandled to the process level, terminating execution.

## 3. Grounded Code Locations & Citations
- File: `apps/kimi-code/src/main.ts` (Lines: `36-75`) | Symbol: `handleMainCommand` | Role: *CLI main command entry point and initialization flow* (Verified: True)
- File: `packages/acp-adapter/src/server.ts` (Lines: `631-670`) | Symbol: `ensureInnerKaos` | Role: *ACP adapter initialization establishing runtime kaos harness* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect handleMainCommand initialization flow**: Inspect handleMainCommand in apps/kimi-code/src/main.ts to locate where configuration and state directory file watchers are established via fs.watch. (Target: `apps/kimi-code/src/main.ts`)
2. **Inspect ensureInnerKaos setup in ACP server**: Inspect ensureInnerKaos in packages/acp-adapter/src/server.ts to identify secondary file system watcher attachments prone to ENOSPC errors. (Target: `packages/acp-adapter/src/server.ts`)
3. **Wrap fs.watch calls with error handlers for ENOSPC**: Add explicit .on('error', ...)` listeners or try/catch blocks around fs.watch invocations in main.ts and server.ts to catch ENOSPC exceptions, log a warning message, and degrade gracefully without crashing. (Target: `apps/kimi-code/src/main.ts`)
4. **Implement regression test and verify with test command**: Add a unit test that mocks fs.watch to emit an ENOSPC error upon initialization and verifies the application handles it gracefully without crashing, then run pnpm test. (Target: `apps/kimi-code/src/main.test.ts`)

## 5. Educational Concepts
### Error Handling and Graceful Degradation
- **What is it:** Catching expected runtime exceptions (like filesystem limits) instead of allowing them to crash the application.
- **Why it matters:** Ensures that minor environmental constraints do not bring down the entire CLI or development tool unexpectedly.
- **Connection to Issue:** File watcher setup needs `try/catch` or error event listeners around `fs.watch` calls to safely handle `ENOSPC` without terminating the process.

### Node.js File System Watchers (fs.watch)
- **What is it:** Node.js built-in API for monitoring changes to files and directories.
- **Why it matters:** Developer tools use file watchers to auto-reload configuration or sync state, but OS limits can restrict the number of active watchers.
- **Connection to Issue:** The crash specifically originates from Node's `fs.watch` failing when system limits are exceeded.

