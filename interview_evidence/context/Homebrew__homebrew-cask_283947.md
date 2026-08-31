# Issue Context Dossier: `Homebrew/homebrew-cask` #283947

**Title:** Ghostty cask started attempting to quit itself, and the updater process, on update.  
**Repository:** https://github.com/Homebrew/homebrew-cask  
**Language:** Ruby  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The `ghostty@tip` cask (and potentially other terminal or shell application casks) started attempting to quit itself and its updater process during standard `brew upgrade -g` updates. Because users run Homebrew commands directly inside terminal emulators like Ghostty, quitting the app kills the terminal emulator and the user's running shells midway through the upgrade, leading to repeated interactive prompts, disrupted workflows, or potential filesystem corruption.

## 2. Root Cause Analysis
> Cask definitions or automated checking/lifecycle utilities (such as `zap_check.rb` or casks declaring `auto_updates true` combined with background quit logic or uninstallation routines) automatically launch, test, or signal running apps to quit to clear state or preferences, inadvertently targeting the active terminal application from which `brew upgrade` is invoked.

## 3. Grounded Code Locations & Citations
- File: `cmd/lib/zap_check.rb` (Lines: `1-40`) | Symbol: `ZapCheck` | Role: *Defines utility mechanisms that launch and quit applications during checks.* (Verified: True)
- File: `cmd/lib/zap_check.rb` (Lines: `71-110`) | Symbol: `ZapCheck.quit` | Role: *Implements application quitting logic via AppleScript/JXA script execution.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect ZapCheck quit logic**: Inspect the ZapCheck.quit implementation in cmd/lib/zap_check.rb to understand how application quit signals and AppleScript termination routines target running processes. (Target: `cmd/lib/zap_check.rb`)
2. **Add self-termination protection check**: Modify the ZapCheck.quit method in cmd/lib/zap_check.rb to check whether the target application matches the current terminal emulator process or the parent session hosting the active Homebrew execution. (Target: `cmd/lib/zap_check.rb`)
3. **Skip self-quitting during active upgrades**: Ensure that if the target bundle identifier or process name matches the active terminal or parent shell session, ZapCheck gracefully skips sending the quit signal or raising interactive prompts. (Target: `cmd/lib/zap_check.rb`)
4. **Add regression test for ZapCheck self-quit prevention**: Add a unit test in the test suite verifying that ZapCheck.quit avoids sending termination signals to the current running terminal session or parent application bundle. (Target: `cmd/lib/zap_check.rb`)
5. **Run test suite verification**: Run the repository test command to verify that all existing and newly added regression tests pass successfully. (Target: `None`)

## 5. Educational Concepts
### Application Lifecycle Management in Casks
- **What is it:** How Homebrew Cask defines metadata, auto-updates, and cleanup behaviors for macOS applications.
- **Why it matters:** Developers need to understand how casks interact with running processes so that automated scripts don't accidentally disrupt active user sessions.
- **Connection to Issue:** Fixing the regression requires ensuring that terminal emulators or host applications are exempted from aggressive self-termination routines during upgrades.

### Process Signaling and AppleScript Automation
- **What is it:** Using system tools and JavaScript for Automation (JXA) to query and quit macOS applications.
- **Why it matters:** Incorrect process targeting can lead to unexpected app closures and data loss.
- **Connection to Issue:** The quit mechanism uses app identifiers to request shutdowns, which currently targets active terminal emulators like Ghostty when running upgrades.

