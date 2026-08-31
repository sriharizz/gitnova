# Issue Context Dossier: `babalae/better-genshin-impact` #3505

**Title:** [bug] 自动秘境寻找古树时更新添加拖拽屏幕后很低概率能够自己领取奖励  
**Repository:** https://github.com/babalae/better-genshin-impact  
**Language:** C#  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The automated domain/ley-line navigation logic for claiming rewards at ancient trees involves dragging the screen while walking. Due to this screen dragging behavior, characters can drift off course, walk into map edges or the abyss, resulting in failed runs and task timeouts. The user requests an option to configure or disable screen dragging during ancient tree reward collection.

## 2. Root Cause Analysis
> The game automation workflow unconditionally invokes screen dragging during navigation steps (e.g., using mouse drag functions in visual flow execution like BvFlow) without a conditional check against user configuration preferences to disable the drag behavior.

## 3. Grounded Code Locations & Citations
- File: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs` (Lines: `526-565`) | Symbol: `block_526` | Role: *Defines mouse drag execution handlers used in automated navigation flow steps.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect screen dragging logic in BvFlow.cs**: Examine block_526 and surrounding methods in BetterGenshinImpact/Core/BgiVision/BvFlow.cs to identify where mouse drag commands are executed during ancient tree reward collection and domain navigation. (Target: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs`)
2. **Introduce configuration check for screen dragging**: Add a configuration setting toggle in the application settings system and incorporate a conditional check before invoking screen drag actions in BvFlow.cs. (Target: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs`)
3. **Implement bypass for screen dragging when disabled**: Update the navigation flow execution logic in BvFlow.cs to bypass or skip mouse drag operations when the new user configuration option is turned off, preventing character drift. (Target: `BetterGenshinImpact/Core/BgiVision/BvFlow.cs`)
4. **Run regression tests and verify behavior**: Execute the test suite to verify that domain navigation functions correctly both with screen dragging enabled and disabled. (Target: `None`)

## 5. Educational Concepts
### Conditional Configuration Flag
- **What is it:** A user-adjustable setting in the configuration model that toggles a specific feature on or off.
- **Why it matters:** Allows automation scripts to adapt to different character heights and environment behaviors without hardcoding assumptions.
- **Connection to Issue:** Enables users to turn off screen dragging during ancient tree navigation if it causes their characters to drift into map boundaries.

### Visual Flow Execution (BvFlow)
- **What is it:** A framework for sequencing visual automation steps including clicks, mouse movements, dragging, and condition waiting.
- **Why it matters:** Manages how automated game actions are chained together into coherent task sequences.
- **Connection to Issue:** The ancient tree finding routine executes drag actions through this flow system, which needs to be conditionally bypassed based on configuration.

