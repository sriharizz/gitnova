# Issue Context Dossier: `babalae/better-genshin-impact` #3456

**Title:** [feedback] 重复点击  
**Repository:** https://github.com/babalae/better-genshin-impact  
**Language:** C#  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The user reports an issue where the automation script repeatedly clicks on a specific interactive object ('臻冰通话器' / Zhenbing Communicator) in a train environment, getting stuck in an infinite click loop that cannot be bypassed even when adding it to a blacklist.

## 2. Root Cause Analysis
> Based on the provided codebase evidence, interaction logic handling click frequency, cooldown tracking, or object filtering lacks robust state checks to prevent re-triggering the same interaction repeatedly within a short time window.

## 3. Grounded Code Locations & Citations
- File: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js` (Lines: `351-373`) | Symbol: `block_351` | Role: *Relevant Code* (Verified: True)
- File: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js` (Lines: `316-355`) | Symbol: `block_316` | Role: *Relevant Code* (Verified: True)
- File: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js` (Lines: `281-320`) | Symbol: `block_281` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect interactive click control flow**: Inspect symbol handling around block_351, block_316, and block_281 in BetterGenshinImpact/GameTask/LogParse/Assets/log.js to understand how interactive object clicks and blacklist checks are currently evaluated. (Target: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js`)
2. **Implement cooldown and debounce mechanism**: Add a timestamp-based cooldown and debounce check in BetterGenshinImpact/GameTask/LogParse/Assets/log.js to prevent rapid repetitive clicking on the same interactive object within a short time window. (Target: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js`)
3. **Enhance blacklist filtering**: Ensure that interactive objects added to the blacklist (such as '臻冰通话器') are correctly evaluated and skipped prior to triggering any interaction actions. (Target: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js`)
4. **Add regression test coverage and verify**: Add a test case verifying that blacklisted items and rapid repeat clicks on interactive objects are properly filtered out and suppressed. (Target: `BetterGenshinImpact/GameTask/LogParse/Assets/log.js`)

## 5. Educational Concepts
### Interaction Debouncing / Cooldown
- **What is it:** A mechanism that prevents an action from being triggered too frequently in quick succession.
- **Why it matters:** Without a cooldown or debounce delay, automated scripts can spam clicks on the same UI element or interactable object before the game state has time to update.
- **Connection to Issue:** Adding a proper cooldown or tracking recently interacted objects prevents the script from repeatedly clicking the Zhenbing Communicator in an infinite loop.

### Blacklist Filtering
- **What is it:** A filtering mechanism that explicitly excludes specific items, targets, or coordinates from being processed by the task runner.
- **Why it matters:** Users rely on blacklists to bypass problematic or stuck objects so that automation can proceed without manual intervention.
- **Connection to Issue:** The issue notes that adding the item to the blacklist does not stop the repetitive clicking, indicating that the blacklist check is either missing, bypassed, or failing to match the target identifier.

