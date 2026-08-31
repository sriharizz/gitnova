# Issue Context Dossier: `babalae/better-genshin-impact` #3496

**Title:** [bug] 制作食物时如果食物材料耗尽，将无限重试  
**Repository:** https://github.com/babalae/better-genshin-impact  
**Language:** C#  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When auto-cooking in BetterGenshinImpact, if ingredients run out mid-process, Genshin Impact automatically exits the cooking screen. However, the BGI task code lacks handling for this state, causing the script to loop indefinitely in retry attempts.

## 2. Root Cause Analysis
> The task workflow executes steps repeatedly or waits for UI elements using flow control mechanisms (such as BvFlow or BvPage) without checking for failure states like inventory exhaustion or unexpected dialog dismissals. When the expected target element disappears or fails to appear due to the lack of ingredients, the loop fails to break out or throw an appropriate termination exception.

## 3. Grounded Code Locations & Citations
- File: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs` (Lines: `211-250`) | Symbol: `Run` | Role: *Flow execution loop handling task steps and exceptions* (Verified: True)
- File: `BetterGenshinImpact/Core/BgiVision/BvPage.cs` (Lines: `1-40`) | Symbol: `BvPage` | Role: *Vision page automation primitives and retry configurations* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Flow Execution Loop in BvFlow.cs**: Examine the Run method in BetterGenshinImpact/Core/BgiVision/BvFlow.cs to understand how step execution and retry loops handle missing UI elements or unexpected interface closures. (Target: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs`)
2. **Analyze Vision Page Automation in BvPage.cs**: Review BvPage in BetterGenshinImpact/Core/BgiVision/BvPage.cs to check how page transitions and timeout/retry configurations are implemented during cooking tasks. (Target: `BetterGenshinImpact/Core/BgiVision/BvPage.cs`)
3. **Implement Ingredient Exhaustion Check**: Add condition checks within the cooking workflow to detect when the cooking interface closes unexpectedly or ingredients run out, terminating the retry loop and throwing an appropriate cancellation exception or notification. (Target: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs`)
4. **Add Regression Test**: Create a regression test simulating the sudden closure of the cooking screen due to missing ingredients to verify that the flow aborts cleanly without infinite loops. (Target: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs`)
5. **Run Test Suite**: Execute the test command to ensure the fix is correct and no regressions are introduced. (Target: `None`)

## 5. Educational Concepts
### Workflow Exception Handling & Termination
- **What is it:** Ensures automation flows can catch unexpected UI state changes and exit cleanly instead of looping forever.
- **Why it matters:** Prevents automation software from locking up or spamming inputs when the game state diverges from expectations.
- **Connection to Issue:** Fixing the infinite retry requires detecting when ingredients run out and throwing a termination exception or gracefully stopping the BvFlow.

### UI State Validation
- **What is it:** Checking whether expected user interface elements or menus remain open before performing actions.
- **Why it matters:** Avoids interacting with stale UI screens or missing windows after in-game events occur.
- **Connection to Issue:** The cooking task needs to verify that the cooking interface is still present before attempting subsequent crafting actions.

