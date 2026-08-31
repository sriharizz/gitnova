# Issue Context Dossier: `facebook/docusaurus` #8938

**Title:** Changing the system theme resets the Docusaurus theme to the default  
**Repository:** https://github.com/facebook/docusaurus  
**Language:** TypeScript  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When the system colour theme changes (via the prefers-color-scheme media query) and respectPrefersColorScheme is disabled, Docusaurus incorrectly resets the site color theme back to default instead of preserving the user's custom preference.

## 2. Root Cause Analysis
> The color mode storage or media query listener logic in theme-common or theme-classic reacts to system theme media query changes without checking whether respectPrefersColorScheme is enabled, causing it to overwrite the user's stored preference with the default fallback.

## 3. Grounded Code Locations & Citations
- File: `packages/docusaurus-theme-classic/src/index.ts` (Lines: `1-40`) | Symbol: `themeClassic` | Role: *Theme classic plugin initialization* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect color mode media query listener**: Inspect the color mode initialization and media query listener logic in packages/docusaurus-theme-classic/src/index.ts and related theme-common modules to locate where prefers-color-scheme changes are handled. (Target: `packages/docusaurus-theme-classic/src/index.ts`)
2. **Verify respectPrefersColorScheme condition**: Verify that when respectPrefersColorScheme is disabled (false), system media query change events do not trigger a reset to the default theme, ensuring the user's manual preference is preserved. (Target: `packages/docusaurus-theme-classic/src/index.ts`)
3. **Update theme-common color mode effect/listener**: Modify the media query listener callback to check the respectPrefersColorScheme configuration value before updating or resetting the active color theme. (Target: `packages/docusaurus-theme-classic/src/index.ts`)
4. **Add regression test and execute test suite**: Add a unit/integration test covering color mode persistence when respectPrefersColorScheme is disabled, and run the test suite to verify the fix. (Target: `packages/docusaurus-theme-classic/src/index.ts`)

## 5. Educational Concepts
### Prefers-Color-Scheme Media Query
- **What is it:** A CSS media feature that detects if the user has requested light or dark color themes through their operating system settings.
- **Why it matters:** It allows websites to automatically adapt to the user's OS-level theme preferences out of the box.
- **Connection to Issue:** The bug occurs because the media query listener listens to OS changes and incorrectly forces a theme reset even when the user has disabled this automatic behavior via respectPrefersColorScheme.

### Color Mode Persistence
- **What is it:** The mechanism by which a web application saves a user's theme choice (light or dark mode) across page reloads using browser storage.
- **Why it matters:** Ensures the user's visual preference is remembered so they don't have to re-select their preferred theme on every page view.
- **Connection to Issue:** The system fails to respect the stored manual preference when an OS-level theme change event fires, overwriting the saved state.

