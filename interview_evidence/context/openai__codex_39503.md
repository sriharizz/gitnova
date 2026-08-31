# Issue Context Dossier: `openai/codex` #39503

**Title:** Approval selector bug, jumps to other value  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When a custom default permissions profile (such as 'project-edit') is configured in `~/.codex/config.toml`, the ChatGPT app shows the custom profile in the approval mode selector. However, clicking other options like 'Approve for me', 'Ask for approval', or 'Full access' causes the UI to immediately revert back to the configured custom profile, making it impossible to change the approval mode dynamically.

## 2. Root Cause Analysis
> The app server or event handling layer receives permission request configurations and parses custom permission profiles (such as `V2GrantedPermissionProfile` or `CoreRequestPermissionProfile`). Due to how permission profiles or defaults are initialized and enforced upon interaction events in `bespoke_event_handling.rs`, the default custom profile is re-applied or incorrectly prioritized over user-selected choices in the active approval flow.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/app-server/src/bespoke_event_handling.rs` (Lines: `1891-1930`) | Symbol: `block_1891` | Role: *Handles permission request approval responses and intersects permission profiles.* (Verified: True)
- File: `codex-rs/app-server/src/bespoke_event_handling.rs` (Lines: `596-635`) | Symbol: `block_596` | Role: *Processes execution approval requests and extracts available decisions.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect permission request approval handling**: Inspect symbol handling in codex-rs/app-server/src/bespoke_event_handling.rs at block_1891 and block_596 to trace how custom default permissions profiles override user-selected approval modes. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
2. **Adjust permission profile enforcement logic**: Modify the event handling logic in codex-rs/app-server/src/bespoke_event_handling.rs so that the configured default custom permissions profile is only used as an initial default, rather than continuously forcing or overwriting user selections when switching approval modes. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
3. **Add regression test for dynamic approval mode selection**: Add a integration or unit test in codex-rs/app-server-test-client/src/lib.rs or related test modules to simulate a custom default profile configuration and verify that selecting alternative approval modes (like 'Approve for me' or 'Full access') is successfully respected and not reverted. (Target: `codex-rs/app-server-test-client/src/lib.rs`)
4. **Run test suite for validation**: Run cargo test for the app-server crate to ensure the fix resolves the overriding behavior and all tests pass successfully. (Target: `None`)

## 5. Educational Concepts
### Permission Profile Intersecting
- **What is it:** The mechanism by which requested permissions and granted user profiles are combined or intersected to enforce security boundaries.
- **Why it matters:** Understanding how default configurations and user selections merge prevents unintended overrides of runtime user choices.
- **Connection to Issue:** Fixing the bug requires ensuring that user-selected approval modes are respected rather than unconditionally forced back to the custom default profile.

### Event-Driven UI State Synchronization
- **What is it:** How backend app server events and frontend selectors synchronize state during approval flows.
- **Why it matters:** Discrepancies between state synchronization cause UI flickering and reverts when user actions conflict with stale default states.
- **Connection to Issue:** The selector jumps back because the backend response or state persistence re-asserts the default profile instead of respecting the newly chosen decision.

