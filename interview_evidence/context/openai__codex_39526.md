# Issue Context Dossier: `openai/codex` #39526

**Title:** Linux ChatGPT desktop app: Pasting text containing “:” with no following space truncates the rest of the line  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Pasting text containing a colon with no following space (e.g. "aaa:bbb") into the Linux ChatGPT desktop app truncates everything from the colon onward.

## 2. Root Cause Analysis
> Clipboard parsing or command line / shlex parsing logic on Linux treats colons or subsequent tokens as special separators or key-value/scheme boundaries without proper escaping or raw string insertion handling.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/app-server/src/command_exec.rs` (Lines: `631-670`) | Symbol: `handle_process_write` | Role: *Relevant Code* (Verified: True)
- File: `codex-rs/app-server/src/bespoke_event_handling.rs` (Lines: `2066-2105`) | Symbol: `None` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect handle_process_write in command_exec.rs**: Examine the handle_process_write function in codex-rs/app-server/src/command_exec.rs to locate where clipboard paste events or process inputs containing colons are parsed or split. (Target: `codex-rs/app-server/src/command_exec.rs`)
2. **Review bespoke event handling logic**: Inspect codex-rs/app-server/src/bespoke_event_handling.rs to check if clipboard string processing or input filtering applies tokenization or scheme parsing on Linux text inputs. (Target: `codex-rs/app-server/src/bespoke_event_handling.rs`)
3. **Fix raw string handling for colons**: Modify the clipboard paste and process writing logic in command_exec.rs to ensure strings containing colons without trailing spaces (e.g. 'aaa:bbb') are treated as literal text instead of split delimiters. (Target: `codex-rs/app-server/src/command_exec.rs`)
4. **Add regression test for clipboard paste with colons**: Update codex-rs/app-server-test-client/src/request_user_input_tests.rs to add a test case verifying that pasting text with colons and no spaces preserves the entire string without truncation. (Target: `codex-rs/app-server-test-client/src/request_user_input_tests.rs`)
5. **Run test suite**: Execute cargo test to verify that all input handling tests pass successfully with the new regression test included. (Target: `None`)

## 5. Educational Concepts
### Clipboard Event Handling and Raw Input Sanitization
- **What is it:** How graphical desktop applications intercept and process clipboard paste events from Wayland and X11 servers.
- **Why it matters:** Developers must ensure that raw clipboard data is treated as literal string input rather than being parsed as structured commands or key-value pairs.
- **Connection to Issue:** Fixing the truncation requires ensuring that clipboard insertion correctly preserves literal characters like colons without triggering command splitting.

### Lexical Tokenization and Command Splitting
- **What is it:** The process of breaking a continuous text stream into distinct tokens using delimiters like spaces or colons.
- **Why it matters:** Incorrect delimiter assumptions lead to data loss when user-entered strings contain punctuation marks.
- **Connection to Issue:** The bug arises because tokenizers or parsers incorrectly split input on colons when no trailing space is present.

