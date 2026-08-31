# Issue Context Dossier: `openai/codex` #41244

**Title:** Codex CLI replays terminal capability queries from persisted tool output on session resume  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Codex CLI replays terminal capability queries (such as device attribute queries) stored in historical PTY or tool output transcripts when resuming a session, causing terminal multiplexers like tmux to interpret them as active queries and inject query responses back into the interactive pane's input stream.

## 2. Root Cause Analysis
> Session restoration replays stored transcript outputs directly without stripping, sanitizing, or neutralizing ANSI/VT100 terminal control sequences and query escape codes (such as ESC [ c), causing active terminal emulators and multiplexers to treat historical data as live incoming escape sequences.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/app-server/src/command_exec.rs` (Lines: `246-285`) | Symbol: `spawn_pty_process` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect PTY spawn and transcript replay logic**: Inspect spawn_pty_process and session resumption handling in codex-rs/app-server/src/command_exec.rs to locate where historical transcript data is replayed or emitted to the terminal. (Target: `codex-rs/app-server/src/command_exec.rs`)
2. **Implement escape sequence sanitization for replayed output**: Introduce a filtering or sanitization utility within codex-rs/app-server/src/command_exec.rs to strip or neutralize terminal control sequences and query escape codes (such as device attribute queries like ESC [ c) prior to writing historical transcript output back to the active terminal or PTY. (Target: `codex-rs/app-server/src/command_exec.rs`)
3. **Add regression test covering session resumption transcript replay**: Add a new integration or unit test in codex-rs/app-server-test-client/src/lib.rs or an appropriate test module that simulates session resumption with historical transcripts containing device attribute queries, verifying that active query responses are not triggered or leaked into the input stream. (Target: `codex-rs/app-server-test-client/src/lib.rs`)
4. **Run test suite to verify fix**: Execute cargo test to verify that all app-server and client tests pass successfully and that the new regression test confirms terminal query sequences are correctly neutralized. (Target: `None`)

## 5. Educational Concepts
### ANSI Escape Sequences & Terminal Capabilities
- **What is it:** Special character sequences starting with an Escape character (ESC) used by terminals to control formatting, cursor positioning, or query hardware/software attributes.
- **Why it matters:** Understanding how terminal emulators interpret escape sequences is critical for preventing security leaks, prompt injection via terminal output, and unintended side effects from replayed transcripts.
- **Connection to Issue:** Resuming a session replays historical tool output containing terminal capability queries, which tmux intercepts and responds to as if they were live interactive queries.

### PTY Output Sanitization
- **What is it:** The process of filtering or neutralizing control characters and escape sequences from pseudo-terminal output streams before they are persisted or rendered.
- **Why it matters:** Ensures that historical terminal logs remain inert text and cannot execute control commands or trigger queries when restored.
- **Connection to Issue:** Fixing the bug requires properly sanitizing or stripping active terminal query sequences from historical tool output during session restoration.

