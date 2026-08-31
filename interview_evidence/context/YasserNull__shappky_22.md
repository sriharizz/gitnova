# Issue Context Dossier: `YasserNull/shappky` #22

**Title:** Google Maps not seen  
**Repository:** https://github.com/YasserNull/shappky  
**Language:** Kotlin  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Google Maps (or similar Google system packages like com.google.android.apps.maps) is not visible in running processes or app listings due to package filtering rules or how system processes/applications are categorized and filtered in ProtectionManager or AppModelFilter.

## 2. Root Cause Analysis
> ProtectionManager includes a specific toggle/group for google packages (`googleEnabled`) which checks if packages start with `com.google.android.`; if this group is disabled or if filtering logic excludes system/Google packages, applications like Google Maps do not appear.

## 3. Grounded Code Locations & Citations
- File: `app/src/main/java/com/yassernull/shappky/core/managers/ProtectionManager.kt` (Lines: `71-110`) | Symbol: `computeEnabledGroupProtectedPackages` | Role: *Handles group protection logic for Google packages starting with com.google.android.* (Verified: True)
- File: `app/src/main/java/com/yassernull/shappky/core/managers/AppModelFilter.kt` (Lines: `71-110`) | Symbol: `buildAllAppsList` | Role: *Filters system, persistent, and protected apps in application lists.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect computeEnabledGroupProtectedPackages control flow**: Examine ProtectionManager.kt around computeEnabledGroupProtectedPackages to verify how package prefixes like com.google.android. are evaluated and whether group toggles like googleEnabled filter out Google Maps. (Target: `app/src/main/java/com/yassernull/shappky/core/managers/ProtectionManager.kt`)
2. **Inspect buildAllAppsList filtering logic**: Review buildAllAppsList in AppModelFilter.kt to ensure system and Google packages are not inadvertently dropped by strict app filtering rules. (Target: `app/src/main/java/com/yassernull/shappky/core/managers/AppModelFilter.kt`)
3. **Adjust Google package inclusion criteria**: Modify package filtering and group protection checks in ProtectionManager.kt and AppModelFilter.kt so that com.google.android.apps.maps and related Google system packages are correctly identified and included. (Target: `app/src/main/java/com/yassernull/shappky/core/managers/ProtectionManager.kt`)
4. **Add regression test and execute suite**: Write a unit test verifying that Google Maps (com.google.android.apps.maps) remains visible in app listings and protection groups, then run the test command to validate. (Target: `app/src/test/java/com/yassernull/shappky/core/managers/ProtectionManagerTest.kt`)

## 5. Educational Concepts
### Android Package Filtering & System Apps
- **What is it:** Android categorizes apps into user apps and system apps, often grouping pre-installed or vendor apps under specific namespaces like com.google.android.*.
- **Why it matters:** Understanding how package namespaces and system flags work ensures tools can correctly locate and display pre-installed applications without hiding them accidentally.
- **Connection to Issue:** Google Maps is a pre-installed system/Google application whose visibility depends on how package filters handle Google namespaces.

### Process Loading and Shell Commands
- **What is it:** The app queries running processes via shell commands like dumpsys and ps and maps them back to Android package names.
- **Why it matters:** If process name matching or regex filtering fails to match a package's process name format, the application will fail to list it as running.
- **Connection to Issue:** Google Maps processes might be filtered out or not matched correctly by the process loader utility.

