# Issue Context Dossier: `unxed/f4` #827

**Title:** Обработка команд меню по клику мыши в редакторе  
**Repository:** https://github.com/unxed/f4  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Mouse clicks on the bottom menu commands in the editor malfunction or stop working properly after toggling Hex Mode, or when the Hex Mode shortcut key is remapped.

## 2. Root Cause Analysis
> Toggling Hex Mode alters terminal modes or input states (such as mouse tracking mode or ANSI parser states handled in ansi_parser.go), but failing to correctly preserve, restore, or reset mouse tracking flags or input handling modes causes subsequent mouse escape sequences to be dropped or misinterpreted.

## 3. Grounded Code Locations & Citations
- File: `cmd/f4/ansi_parser.go` (Lines: `771-810`) | Symbol: `handleDECRQM` | Role: *ANSI Parser mode handling and state queries* (Verified: True)
- File: `cmd/f4/ansi_parser.go` (Lines: `561-600`) | Symbol: `AnsiParser` | Role: *DECSET / DECRST mode switching including mouse tracking modes* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect handleDECRQM and AnsiParser mode state handling**: Inspect handleDECRQM and DECSET / DECRST mode switching logic in cmd/f4/ansi_parser.go to identify how mouse tracking modes and parser states are toggled or reset during Hex Mode transitions. (Target: `cmd/f4/ansi_parser.go`)
2. **Fix mouse tracking mode preservation and reset logic**: Update the state handling in AnsiParser within cmd/f4/ansi_parser.go to correctly preserve and restore mouse tracking flags when toggling or remapping Hex Mode, preventing escape sequence desynchronization. (Target: `cmd/f4/ansi_parser.go`)
3. **Add regression tests in ansi_parser_test.go**: Add comprehensive unit tests in cmd/f4/ansi_parser_test.go verifying that mouse tracking modes remain correctly synchronized and active after toggling Hex Mode or remapping its shortcut key. (Target: `cmd/f4/ansi_parser_test.go`)
4. **Run test suite to verify fix**: Run go test ./cmd/f4/... to validate that all ansi parser and synchronization tests pass successfully without regressions. (Target: `cmd/f4/ansi_parser_test.go`)

## 5. Educational Concepts
### Terminal Mouse Tracking Modes
- **What is it:** ANSI escape sequences (like modes 1000, 1002, 1003) that instruct the terminal emulator to report mouse clicks and movements as escape sequences back to the application.
- **Why it matters:** Without proper mouse tracking mode management, clicks on interactive UI elements like bottom menus will either be ignored or treated as raw text characters.
- **Connection to Issue:** Toggling Hex Mode or changing its keybinding interferes with or resets the terminal state machine managing mouse tracking escape sequences.

### ANSI Mode State Synchronization
- **What is it:** Ensuring that internal application state variables and terminal emulator modes remain perfectly synchronized during mode switches.
- **Why it matters:** Desynchronization between what the editor thinks the terminal mode is and what the parser or terminal actually enforces leads to broken input handling.
- **Connection to Issue:** Switching Hex Mode modifies terminal states, but failure to properly re-apply or maintain mouse reporting modes causes subsequent mouse clicks to fail.

