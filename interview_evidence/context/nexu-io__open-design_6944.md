# Issue Context Dossier: `nexu-io/open-design` #6944

**Title:** Guard DeepSeek Harness native-session resume with a compatibility generation  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When the daemon decides whether to resume a previously saved agent session (such as DeepSeek Harness), it checks if the model, current working directory (cwd), and conversation cursor match. However, if the underlying agent's executable, plugin version, or configuration (compatibility generation) changes, the session might be incompatible. Currently, the daemon does not store or check this compatibility generation, meaning it will incorrectly try to resume a session even after an upgrade or configuration change, leading to potential runtime errors.

## 2. Root Cause Analysis
> The root cause is a lack of persistence and validation of the compatibility generation in the session resume control flow. Specifically:
1. The SQLite schema for `agent_sessions` in `apps/daemon/src/db.ts` lacks a column to store compatibility metadata (e.g., `compatibility_generation`).
2. `getAgentSessionRecord` and `persistCapturedAgentSession` in `apps/daemon/src/db.ts` and `apps/daemon/src/agent-session-resume.ts` do not read, write, or pass any compatibility generation parameter.
3. `evaluateResumeInvalidation` only compares `storedModel` vs `currentModel` and `storedCwd` vs `currentCwd`.
4. Because run construction resolves the resume decision before spawning the profile, and the spawned profile's actual identity/compatibility is only verified at `ready` time, the daemon cannot proactively invalidate the resume path when a changed-but-loadable runtime composition is introduced.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/db.ts` (Lines: `176-215`) | Symbol: `agent_sessions` | Role: *Database schema definition for agent sessions* (Verified: True)
- File: `apps/daemon/src/db.ts` (Lines: `2416-2455`) | Symbol: `getAgentSessionRecord` | Role: *Retrieves the persisted agent session record from SQLite* (Verified: True)
- File: `apps/daemon/src/agent-session-resume.ts` (Lines: `71-110`) | Symbol: `resolveAgentResumeContext` | Role: *Evaluates whether a session can be resumed based on model, cwd, and cursor* (Verified: True)
- File: `apps/daemon/src/agent-session-resume.ts` (Lines: `106-145`) | Symbol: `persistCapturedAgentSession` | Role: *Persists a captured agent session to the database* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Schema and Resume Logic**: Inspect the `agent_sessions` table schema and the `getAgentSessionRecord` function in `apps/daemon/src/db.ts`. Also, inspect `resolveAgentResumeContext` and `evaluateResumeInvalidation` in `apps/daemon/src/agent-session-resume.ts` to understand how session parameters are currently compared. (Target: `apps/daemon/src/db.ts`)
2. **Update Database Schema and Persistence**: Modify the `agent_sessions` table definition in `apps/daemon/src/db.ts` to include a new column `compatibility_generation` (TEXT). Update `getAgentSessionRecord` and `persistCapturedAgentSession` to read and write this new field. (Target: `apps/daemon/src/db.ts`)
3. **Implement Compatibility Validation**: Update `resolveAgentResumeContext` and `evaluateResumeInvalidation` in `apps/daemon/src/agent-session-resume.ts` to accept the current agent's compatibility generation. Compare this value against the stored `compatibility_generation` from the database. If they do not match, or if the stored value is missing, invalidate the session by setting `isResuming` to false. (Target: `apps/daemon/src/agent-session-resume.ts`)
4. **Add Regression Tests**: Create or update tests in `apps/daemon/src/connectionTest.ts` (or a dedicated test file) to verify that a session is successfully resumed when the compatibility generation matches, and is correctly invalidated when the compatibility generation changes. (Target: `apps/daemon/src/connectionTest.ts`)

## 5. Educational Concepts
### Session Resume Guard
- **What is it:** A mechanism that ensures a saved agent session is only resumed if the environment and conversation state are completely compatible with when the session was saved.
- **Why it matters:** Without proper resume guards, an agent might resume a session with mismatched assumptions (e.g., different working directory, different model, or different tool versions), leading to silent failures, corrupted states, or crashes.
- **Connection to Issue:** The issue is that the current resume guard only checks model, cwd, and message cursor, but misses the agent's compatibility generation (executable identity, protocol version, and composition). We need to extend the resume guard to include this compatibility generation.

### Database Schema Migration & Evolution
- **What is it:** The process of updating the database structure (like adding a new column to an existing table) to support new features while preserving existing data.
- **Why it matters:** As applications grow, the data we need to persist changes. Developers must update table schemas and the corresponding read/write queries carefully to avoid breaking existing installations or causing data loss.
- **Connection to Issue:** To fix this issue, we must add a new column (e.g., `compatibility_generation`) to the `agent_sessions` table in SQLite, and update the database helper functions to read and write this new field.

