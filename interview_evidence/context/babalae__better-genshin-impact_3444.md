# Issue Context Dossier: `babalae/better-genshin-impact` #3444

**Title:** 希望把桌面分身的小窗模式的还原单独加快捷按键  
**Repository:** https://github.com/babalae/better-genshin-impact  
**Language:** C#  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The user is requesting a shortcut key or a dedicated button to restore the desktop clone window ('桌面分身的小窗模式') from its mini/small window mode back to its normal state, avoiding the need to go through a nested submenu every time.

## 2. Root Cause Analysis
> The current feature implementation for desktop clone small-window mode provides only nested context or sub-menu options for window restoration without binding a quick action key or direct UI button.

## 3. Grounded Code Locations & Citations
- *General repository target scope*

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Desktop Clone Window Controls**: Inspect the desktop clone window controls and sub-menu implementation to locate where small-window mode and restoration actions are handled. (Target: `None`)
2. **Add Direct Restoration Button or Shortcut Command**: Implement a direct UI button or bind a shortcut key to trigger the desktop clone window restoration from mini mode back to normal size. (Target: `None`)
3. **Add Regression Test**: Write a regression test ensuring that activating the restoration shortcut or clicking the direct button successfully transitions the desktop clone window from small-window mode to normal state. (Target: `None`)
4. **Run Test Suite**: Execute the build and test suite to verify that the desktop clone window restoration works correctly without regressions. (Target: `None`)

## 5. Educational Concepts
### UI Window State Toggle
- **What is it:** Managing different display states (minimized, small window, normal) of an application or clone window.
- **Why it matters:** Provides users with flexible control over how they monitor and interact with background tasks or cloned game instances.
- **Connection to Issue:** Directly relates to adding a quick toggle or shortcut mechanism to transition the desktop clone between small window mode and normal mode.

### Keyboard Shortcut Binding
- **What is it:** Mapping global or local key combinations to trigger specific application actions.
- **Why it matters:** Enables users to perform frequent operations quickly without navigating through menus using a mouse.
- **Connection to Issue:** Fulfills the user request for a dedicated shortcut key to restore the window state.

