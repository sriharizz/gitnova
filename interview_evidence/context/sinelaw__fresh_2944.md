# Issue Context Dossier: `sinelaw/fresh` #2944

**Title:** SSH files marked read-only when local and remote UIDs differ  
**Repository:** https://github.com/sinelaw/fresh  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> SSH files are incorrectly marked read-only when the local Fresh process and remote SSH user have different numeric user IDs (UID) or group IDs (GID), because file ownership checks compare remote file metadata against the local user's identity instead of the remote SSH user's identity.

## 2. Root Cause Analysis
> The editor's file accessors or metadata checks evaluate permissions against local user credentials or misattribute remote file ownership to the local host's authority context instead of delegating the permission check entirely to the remote filesystem connection's authority.

## 3. Grounded Code Locations & Citations
- File: `crates/fresh-editor/src/app/editor_accessors.rs` (Lines: `1226-1265`) | Symbol: `remote_connection_info` | Role: *Handles remote connection inspection and authority context retrieval* (Verified: True)
- File: `crates/fresh-editor/src/main.rs` (Lines: `1471-1510`) | Symbol: `parse_location` | Role: *Parses remote SSH URLs and default user credentials* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Remote Connection and Permission Logic**: Inspect remote_connection_info and related accessor methods in crates/fresh-editor/src/app/editor_accessors.rs to determine how file writability and ownership checks are currently evaluated against local user credentials rather than the remote SSH user. (Target: `crates/fresh-editor/src/app/editor_accessors.rs`)
2. **Delegate Permission Evaluation to Remote Authority**: Modify the file writability check in crates/fresh-editor/src/app/editor_accessors.rs so that remote SSH connections correctly evaluate file permissions and ownership using the remote SSH user identity instead of falling back to local host UIDs/GIDs. (Target: `crates/fresh-editor/src/app/editor_accessors.rs`)
3. **Write Regression Test for Mismatched UIDs**: Add a unit or integration test case in the test suite verifying that remote files accessed via SSH with differing local and remote UIDs are correctly marked as writable when permissions allow, preventing false read-only triggers. (Target: `crates/fresh-editor/src/app/editor_accessors.rs`)
4. **Run Test Suite and Verify Fix**: Run the verified test command cargo test to ensure all tests pass successfully without any regressions in local or remote file editing behavior. (Target: `None`)

## 5. Educational Concepts
### Remote Authority and Identity Delegation
- **What is it:** Ensuring that operations and permission checks on remote systems use the remote session's user identity rather than local process credentials.
- **Why it matters:** Different machines or containers (such as Termux environments) assign arbitrary numeric UIDs to users, so comparing local and remote UIDs causes false permission mismatches.
- **Connection to Issue:** Fixing this issue requires ensuring remote file writability checks rely on the remote session authority rather than local user IDs.

### Automatic Read-Only Detection
- **What is it:** An editor feature that automatically marks files read-only if the current user lacks write permissions.
- **Why it matters:** It prevents users from accidentally editing files they cannot save, but it depends on accurate permission checks.
- **Connection to Issue:** Because permission checks incorrectly use local UIDs for remote files, auto-read-only incorrectly locks valid remote files.

