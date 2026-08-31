# Issue Context Dossier: `openai/codex` #39636

**Title:** `/fast` is a toggle, this is terrible.  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The `/fast` command acts purely as a toggle instead of accepting explicit state modifiers like `/fast off` or `/fast on`, which causes users to inadvertently remain in fast mode and exhaust rate limits.

## 2. Root Cause Analysis
> The CLI command parsing logic for `/fast` interprets the input solely as a binary switch flag without parsing sub-arguments (such as `off` or `on`) to set an absolute target state.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/app-server/src/bespoke_event_handling.rs` (Lines: `2136-2175`) | Symbol: `None` | Role: *App server event handling and command orchestration context* (Verified: True)
- File: `codex-rs/app-server-client/src/lib.rs` (Lines: `176-215`) | Symbol: `None` | Role: *App server client configuration and command state context* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Fast Command Parsing Logic**: Inspect symbol handling for the `/fast` command in codex-rs/app-server/src/bespoke_event_handling.rs to verify how arguments are currently ignored and the state is toggled. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
2. **Parse Optional Arguments for State Modifiers**: Update the command parser in codex-rs/app-server/src/bespoke_event_handling.rs to accept optional 'on' or 'off' arguments following the `/fast` command. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
3. **Implement Absolute State Setting**: Modify the execution branch to set the fast mode state explicitly based on the parsed argument ('on' -> true, 'off' -> false) while preserving bare toggle behavior when no argument is supplied. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
4. **Add Regression Tests for Explicit Fast State Modifiers**: Add unit and integration tests verifying that `/fast on`, `/fast off`, and bare `/fast` correctly set the expected fast mode state. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)

## 5. Educational Concepts
### Command Argument Parsing
- **What is it:** The process of reading text input after a command slash and extracting parameters or sub-commands.
- **Why it matters:** Developers need precise control over CLI options so they can specify exact states rather than guessing toggle states.
- **Connection to Issue:** Fixing the issue requires parsing optional arguments like 'on' or 'off' following the `/fast` command rather than treating it as a bare toggle.

### Idempotent State Setters vs Toggles
- **What is it:** Toggles flip the current state blindly, whereas idempotent setters ensure the system reaches a specific known state regardless of prior state.
- **Why it matters:** Idempotency prevents user error and resource waste caused by mismatched assumptions about current system state.
- **Connection to Issue:** Users expect `/fast off` to be an idempotent setter that guarantees fast mode is disabled, preventing accidental rate-limit exhaustion.

