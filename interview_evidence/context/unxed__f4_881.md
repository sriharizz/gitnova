# Issue Context Dossier: `unxed/f4` #881

**Title:** Выделение в Терминале  
**Repository:** https://github.com/unxed/f4  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When text is selected in the terminal, pressing any key clears the selection and copies it to the clipboard (similar to pressing Ctrl+C), making it impossible to deselect or cancel the selection without copying.

## 2. Root Cause Analysis
> The terminal emulator handles incoming keypress events and mouse/selection states without checking if an active selection should be dismissed on specific keys like Escape. Instead, key events or input state handlers aggressively trigger copy or clear-selection actions prematurely.

## 3. Grounded Code Locations & Citations
- File: `cmd/f4/ansi_parser.go` (Lines: `281-320`) | Symbol: `AnsiParser` | Role: *Relevant Code* (Verified: True)
- File: `cmd/f4/ansi_parser.go` (Lines: `456-495`) | Symbol: `handleCSI` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Terminal Key and Selection Handling**: Inspect symbol handleCSI and related input handling logic in cmd/f4/ansi_parser.go to understand how keypress events interact with the active terminal text selection. (Target: `cmd/f4/ansi_parser.go`)
2. **Prevent Automatic Copy on Escape Keypress**: Modify the keypress event handler in cmd/f4/ansi_parser.go to check if the incoming key is Escape; if an active selection exists, dismiss/clear the selection without triggering a copy-to-clipboard action. (Target: `cmd/f4/ansi_parser.go`)
3. **Add Regression Test in Test Suite**: Update cmd/f4/ansi_parser_test.go to add a new test case simulating text selection followed by pressing Escape, asserting that the selection is cleared and clipboard copy is not triggered. (Target: `cmd/f4/ansi_parser_test.go`)
4. **Run Test Suite to Verify Fix**: Execute the test command to verify that all existing tests pass and the new regression test successfully validates the updated selection-clearing behavior. (Target: `None`)

## 5. Educational Concepts
### Terminal Selection State Handling
- **What is it:** Managing how text highlighting and mouse selection interact with keyboard input events in a terminal emulator.
- **Why it matters:** Users need predictable control over text selection so they can inspect text or cancel selections without accidentally triggering clipboard copy operations.
- **Connection to Issue:** The issue stems from key events unconditionally clearing and copying selections instead of allowing keys like Escape to simply dismiss the selection.

### Input Event Dispatching
- **What is it:** The mechanism by which keyboard strokes and escape sequences are captured and routed to specific terminal actions.
- **Why it matters:** Correct event routing ensures that control keys (like Esc) perform cancellation or navigation tasks rather than mutating buffer or selection states incorrectly.
- **Connection to Issue:** Fixing the bug requires intercepting specific key inputs (such as Escape) in the event dispatch loop to clear the selection state without invoking clipboard copy routines.

