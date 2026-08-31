# Issue Context Dossier: `mixxxdj/mixxx` #16859

**Title:** waveform: option to invert zoom direction for mousewheel scroll?  
**Repository:** https://github.com/mixxxdj/mixxx  
**Language:** C++  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The user is requesting a feature in the waveform preferences to add a radio-box or setting option to invert the zoom direction when scrolling with the mousewheel over the waveform.

## 2. Root Cause Analysis
> The preference option for inverting mousewheel zoom direction on waveforms is currently unimplemented or was previously dropped during earlier merges (#9952, #4195), meaning the zoom delta calculation does not check any user configuration flag for inversion.

## 3. Grounded Code Locations & Citations
- File: `src/mixxxmainwindow.cpp` (Lines: `316-355`) | Symbol: `MixxxMainWindow` | Role: *Preferences dialog initialization and connection* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect waveform preference settings and zoom handling**: Examine src/mixxxmainwindow.cpp and related waveform preference configuration files to locate mousewheel zoom delta computation and existing preference connections. (Target: `src/mixxxmainwindow.cpp`)
2. **Add preference option for inverting waveform mousewheel zoom**: Introduce a configuration setting and corresponding radio-box or checkbox option in the waveform preferences dialog UI/backend logic to allow users to toggle zoom inversion. (Target: `src/mixxxmainwindow.cpp`)
3. **Apply zoom inversion logic based on preference flag**: Update the mousewheel scroll event handler for the waveform display to check the new preference flag and invert the zoom delta calculation accordingly. (Target: `src/mixxxmainwindow.cpp`)
4. **Add regression tests and execute test suite**: Add unit tests verifying that toggling the invert mousewheel zoom preference correctly alters the sign or direction of the resulting zoom delta, then run the test suite to confirm. (Target: `src/mixxxmainwindow.cpp`)

## 5. Educational Concepts
### User Preferences Integration
- **What is it:** Storing and retrieving user-configurable settings through Mixxx's settings management system.
- **Why it matters:** Allows user interface components and event handlers to adapt their runtime behavior based on individual user workflow preferences.
- **Connection to Issue:** An invert zoom preference needs to be stored in the settings backend and read when handling mousewheel scroll events on the waveform.

### Mousewheel Event Handling
- **What is it:** Intercepting and responding to QWheelEvent objects in Qt widgets to control scaling or scrolling.
- **Why it matters:** Enables interactive visual feedback like zooming in and out when users scroll their mouse over graphical widgets.
- **Connection to Issue:** The mousewheel event handler for the waveform widget must multiply the scroll delta by -1 when the invert zoom preference is enabled.

