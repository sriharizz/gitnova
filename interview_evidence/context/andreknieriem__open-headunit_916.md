# Issue Context Dossier: `andreknieriem/open-headunit` #916

**Title:** Home screen layout bug after editing vehicle information  
**Repository:** https://github.com/andreknieriem/open-headunit  
**Language:** Kotlin  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Issue #916 reports a home screen layout bug that occurs after editing vehicle information in the app's settings and returning to the home screen.

## 2. Root Cause Analysis
> The root cause stems from configuration or state changes (such as updated vehicle name/information or screen dimension/UI configuration updates) not correctly triggering a proper UI refresh or layout pass when returning from the settings fragment/activity.

## 3. Grounded Code Locations & Citations
- File: `app/src/main/java/com/andrerinas/openheadunit/aap/AapProjectionActivity.kt` (Lines: `975-985`) | Symbol: `commManager.onUpdateUiConfigReplyReceived` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect UI configuration update flow**: Inspect symbol commManager.onUpdateUiConfigReplyReceived in app/src/main/java/com/andrerinas/openheadunit/aap/AapProjectionActivity.kt to understand how UI configuration changes and layout passes are triggered when returning from settings. (Target: `app/src/main/java/com/andrerinas/openheadunit/aap/AapProjectionActivity.kt`)
2. **Ensure layout re-initialization on resume or configuration update**: Update AapProjectionActivity.kt to trigger a complete UI layout refresh or request layout pass when returning from the settings fragment/activity after vehicle information changes. (Target: `app/src/main/java/com/andrerinas/openheadunit/aap/AapProjectionActivity.kt`)
3. **Add regression test for home screen layout synchronization**: Implement a test case verifying that returning to the home screen after saving vehicle settings correctly preserves the expected UI dimensions and layout alignment. (Target: `app/src/main/java/com/andrerinas/openheadunit/aap/AapProjectionActivity.kt`)
4. **Run test suite to verify fix**: Execute the project test suite using the suggested gradle command to ensure no regressions are introduced. (Target: `None`)

## 5. Educational Concepts
### Activity and Fragment Lifecycle State Management
- **What is it:** How Android components coordinate UI updates and state persistence when navigating between screens.
- **Why it matters:** Understanding lifecycle methods like onResume() and onPause() ensures that UI components reflect the latest configuration changes when returning from settings.
- **Connection to Issue:** When returning from the settings screen after editing vehicle information, the home screen or projection activity needs to correctly handle configuration changes and re-layout views.

### UI Configuration and Layout Updates
- **What is it:** Mechanisms responsible for adjusting screen margins, dimensions, and layout elements dynamically.
- **Why it matters:** Proper UI configuration handling prevents visual artifacts and incorrect scaling or positioning on different head unit displays.
- **Connection to Issue:** The layout bug manifests visually after saving settings, indicating that UI configuration parameters or view hierarchies need a refresh upon return.

