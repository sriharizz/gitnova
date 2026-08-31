# Issue Context Dossier: `mixxxdj/mixxx` #14903

**Title:** update skins to provide 16 hotcue skin setting?  
**Repository:** https://github.com/mixxxdj/mixxx  
**Language:** C++  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The contributor wants to update the Deere skin configuration in Mixxx to support 16 hotcues and provide radio box style mutually exclusive skin settings.

## 2. Root Cause Analysis
> Skins are defined via XML and skin-loading configuration mechanisms that currently lack support for 16 hotcues and radio-group mutually exclusive preferences in their layout definitions.

## 3. Grounded Code Locations & Citations
- File: `src/mixxxmainwindow.cpp` (Lines: `1415-1440`) | Symbol: `loadConfiguredSkin` | Role: *Skin loading entry point* (Verified: True)
- File: `src/mixxxmainwindow.h` (Lines: `106-145`) | Symbol: `MixxxMainWindow` | Role: *Window header declaring skin management references* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect skin loading and configuration logic**: Inspect symbol loadConfiguredSkin in src/mixxxmainwindow.cpp and src/mixxxmainwindow.h to understand how skin settings and hotcue options are initialized and parsed. (Target: `src/mixxxmainwindow.cpp`)
2. **Update Deere skin XML configuration for 16 hotcues**: Modify the Deere skin definition files to include support for 16 hotcues by extending the hotcue grid and related control bindings. (Target: `res/skins/Deere/`)
3. **Implement radio-box style mutually exclusive skin settings**: Update skin settings logic to support radio-box style behavior ensuring mutually exclusive selections among designated skin options. (Target: `src/mixxxmainwindow.cpp`)
4. **Run tests and verify implementation**: Run the test suite using pre-commit or the repository test command to verify that skin loading and the new Deere 16 hotcue configuration work correctly without regressions. (Target: `None`)

## 5. Educational Concepts
### Mixxx Skin Configuration
- **What is it:** Mixxx skins use XML layout files and configuration options to define UI elements, decks, waveforms, and controls like hotcues.
- **Why it matters:** Developers need to understand skin definitions to add new layout features and user-selectable options.
- **Connection to Issue:** Directly relates to adding 16 hotcues and updating skin setting options within the Deere skin definition.

### Mutually Exclusive UI Settings (Radio Box)
- **What is it:** A UI control pattern where a group of options allows only a single selection at any given time.
- **Why it matters:** Ensures users cannot select conflicting configuration states simultaneously.
- **Connection to Issue:** Addresses the feature request for radio box style only-one-selected options in skin settings.

