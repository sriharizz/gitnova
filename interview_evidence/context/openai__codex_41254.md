# Issue Context Dossier: `openai/codex` #41254

**Title:** [Codex Desktop][macOS][Voice] Delivered turns remain in failed Retry queue  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Voice turns in the Codex desktop app successfully deliver substantive text to the active chat context, but erroneously remain in the composer/queue as failed items featuring retry actions and exclamation indicators.

## 2. Root Cause Analysis
> Incoming voice or turn delivery events fail to update or clear their queue/composer state correctly upon successful processing, causing successfully delivered items to retain a persistent error or failure flag.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/analytics/src/client.rs` (Lines: `736-775`) | Symbol: `block_736` | Role: *Turn completion and error handling logic mapping event statuses* (Verified: True)
- File: `codex-rs/app-server/src/bespoke_event_handling.rs` (Lines: `3886-3925`) | Symbol: `block_3886` | Role: *App server handling of turn completion and failed turn status representation* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect turn completion and event status handling**: Inspect the turn completion and error handling logic mapping event statuses in codex-rs/analytics/src/client.rs around block_736 and codex-rs/app-server/src/bespoke_event_handling.rs around block_3886. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
2. **Update voice turn event delivery state handling**: Modify the event handler in codex-rs/app-server/src/bespoke_event_handling.rs to ensure successfully delivered voice turns clear their queue or composer state instead of retaining a failed/retry status flag. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
3. **Refine client status mapping logic**: Adjust the event status mapping in codex-rs/analytics/src/client.rs around block_736 to properly distinguish successful transcript delivery from error states. (Target: `codex-rs/analytics/src/client.rs`)
4. **Add regression test coverage**: Implement a regression test verifying that successfully processed voice turns are cleanly removed from the composer/queue without showing retry indicators or failure states. (Target: `codex-rs/analytics/src/analytics_client_tests.rs`)
5. **Run test suite verification**: Execute cargo test to verify all analytics and app-server integration tests pass successfully without regressions. (Target: `None`)

## 5. Educational Concepts
### Turn Lifecycle Status Synchronization
- **What is it:** Ensuring that the status of a user turn tracked in application state matches its actual execution result in the backend.
- **Why it matters:** Mismatches between actual delivery and UI representation cause confusing false errors and redundant retries.
- **Connection to Issue:** Voice turns successfully deliver text to the chat context but remain stuck in a failed state because their completion status propagation fails to clear the pending queue item.

### Error Flag Propagation
- **What is it:** The mechanism by which error objects or failure flags are attached to asynchronous event notifications.
- **Why it matters:** Incorrectly attaching or failing to clear error flags results in UI components falsely treating successful operations as failures.
- **Connection to Issue:** Voice turn delivery events may be incorrectly initialized with or retaining error structures even when execution completes successfully.

