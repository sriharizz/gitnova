# Issue Context Dossier: `MoonshotAI/kimi-code` #3178

**Title:** [Bug] Swarm 运行中执行 /usage 后，实时进度面板不再可见  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When running an AgentSwarm in the Kimi Code CLI, executing the `/usage` command causes the live progress panel for the swarm to disappear from the interface, leaving it invisible even though background tasks continue to execute.

## 2. Root Cause Analysis
> Due to overlapping UI overlay/panel rendering logic when a transient command panel like `/usage` is invoked, active sticky status components such as the AgentSwarm progress tracker are improperly cleared or not re-rendered upon command completion.

## 3. Grounded Code Locations & Citations
- File: `apps/kimi-code/src/main.ts` (Lines: `1-110`) | Symbol: `main` | Role: *Application entry point and runner delegation* (Verified: True)
- File: `apps/kimi-inspect/src/panels.ts` (Lines: `36-75`) | Symbol: `CORE_PANELS` | Role: *Service panel definitions and agent swarm integration* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect AgentSwarm Progress Panel Rendering and Command Overlays**: Examine CORE_PANELS and active swarm progress tracking logic in apps/kimi-inspect/src/panels.ts and apps/kimi-code/src/main.ts to understand how transient command panels like /usage clear or suppress sticky UI components. (Target: `apps/kimi-inspect/src/panels.ts`)
2. **Preserve Swarm Progress State During Transient Command Execution**: Modify the panel toggle and rendering sequence in apps/kimi-code/src/main.ts so that executing /usage does not permanently unmount or suppress the AgentSwarm live progress panel. (Target: `apps/kimi-code/src/main.ts`)
3. **Restore Swarm Visibility After Command Completion**: Ensure that when the /usage panel is dismissed or closed, the active AgentSwarm progress tracker automatically re-renders and reasserts its sticky position above the input box. (Target: `apps/kimi-inspect/src/panels.ts`)
4. **Add Regression Test for Swarm Panel Persistence**: Write a test case verifying that running an AgentSwarm and invoking /usage keeps or properly restores the swarm progress panel upon command exit. (Target: `apps/kimi-code/src/main.ts`)
5. **Run Test Suite for Verification**: Execute the repository test suite via pnpm test to ensure all tests pass and no UI regression occurs. (Target: `None`)

## 5. Educational Concepts
### CLI View State Management
- **What is it:** Managing how different overlapping panels, prompts, and persistent status bars render in a terminal UI.
- **Why it matters:** Ensures that transient diagnostic commands (like `/usage`) do not permanently overwrite or dismiss long-running background progress indicators.
- **Connection to Issue:** Fixes the bug where invoking `/usage` causes the persistent AgentSwarm progress panel to vanish permanently from the screen.

### Active Service State Polling
- **What is it:** Tracking and querying active background services like agent swarms to decide whether their progress UI should be displayed.
- **Why it matters:** Allows the UI to correctly re-render active background tasks after a transient view or command closes.
- **Connection to Issue:** Ensures that after `/usage` completes or closes, the UI checks the active swarm state and restores the progress panel.

