# Issue Context Dossier: `MoonshotAI/kimi-code` #3147

**Title:** feat(kimi-web): add a collapse button at the bottom (or floating) of long expanded blocks  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The issue requests adding a bottom or floating collapse button/control for long expanded blocks (such as thinking, work-in-progress groups, tool call details) in the kimi web session view, so that users do not have to scroll back to the top of the block to collapse it.

## 2. Root Cause Analysis
> UI components rendering collapsible content containers (such as JSON viewers or inspect panels) currently lack bottom-of-block collapse triggers or sticky/floating headers when the content exceeds viewport height.

## 3. Grounded Code Locations & Citations
- File: `apps/kimi-inspect/src/ui.tsx` (Lines: `1-40`) | Symbol: `JsonView` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect JsonView Component in ui.tsx**: Examine the JsonView component implementation in apps/kimi-inspect/src/ui.tsx to understand how collapsible content containers and their top collapse controls are currently rendered. (Target: `apps/kimi-inspect/src/ui.tsx`)
2. **Add Bottom Collapse Control to JsonView**: Modify the JsonView component in apps/kimi-inspect/src/ui.tsx to conditionally render a secondary collapse button at the bottom of the expanded block when content length exceeds a threshold or when the block is expanded. (Target: `apps/kimi-inspect/src/ui.tsx`)
3. **Write Regression Test for Bottom Collapse Control**: Add a unit or integration test verifying that the bottom collapse button renders correctly inside expanded blocks in JsonView and successfully collapses the component when triggered. (Target: `apps/kimi-inspect/src/ui.tsx`)
4. **Run Test Suite**: Execute the verified test command to ensure the new bottom collapse feature passes and no existing tests are broken. (Target: `None`)

## 5. Educational Concepts
### Viewport Scrolling and Sticky UI Elements
- **What is it:** Techniques used in web interfaces to keep interactive controls accessible when content overflows the screen height.
- **Why it matters:** Improves user experience by eliminating tedious scrolling when interacting with long-form content blocks.
- **Connection to Issue:** Directly addresses the requirement for bottom collapse buttons or sticky floating controls when long blocks are expanded.

### Component State Management for UI Controls
- **What is it:** Using local component state (like React useState) to track whether a section is expanded or collapsed.
- **Why it matters:** Allows UI elements to dynamically render interaction buttons and change layout classes based on user actions.
- **Connection to Issue:** Enables toggle handlers at both top and bottom controls to modify the open/closed state of long content blocks.

