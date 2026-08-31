# Issue Context Dossier: `MoonshotAI/kimi-code` #3379

**Title:** KIMI Vscode 插件，输入 /[skill-name] 后，按下 tab 键不是补全，是直接发送出去了  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> In the Kimi VSCode extension, typing a slash command like `/[skill-name]` followed by the `Tab` key incorrectly submits the chat message instead of triggering autocompletion or selecting the active skill suggestion.

## 2. Root Cause Analysis
> The issue stems from the keydown event handling in the webview's chat input interface (likely handling `Tab` and `Enter` key codes), where default key behaviors are not intercepted to prevent message submission when autocomplete menus or skill popups are open.

## 3. Grounded Code Locations & Citations
- File: `apps/vscode/src/extension.ts` (Lines: `106-145`) | Symbol: `activate` | Role: *Extension activation and command registration* (Verified: True)
- File: `apps/vscode/src/KimiWebviewProvider.ts` (Lines: `1-40`) | Symbol: `KimiWebviewProvider` | Role: *Manages webview instances and message passing* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect webview keydown event handler**: Examine symbol KimiWebviewProvider and its webview message or HTML template generation in apps/vscode/src/KimiWebviewProvider.ts to locate where keyboard events ('Tab' and 'Enter') for chat input and slash command autocompletion are bound. (Target: `apps/vscode/src/KimiWebviewProvider.ts`)
2. **Intercept Tab and Enter keys during active skill suggestion**: Modify the keydown listener in the webview script within KimiWebviewProvider.ts to check if a slash command or skill suggestion dropdown is currently open and active, preventing default message submission on Tab or Enter. (Target: `apps/vscode/src/KimiWebviewProvider.ts`)
3. **Verify extension activation and command setup**: Inspect activate in apps/vscode/src/extension.ts to ensure webview provider registration and command message listeners correctly handle selection messages from the webview UI. (Target: `apps/vscode/src/extension.ts`)
4. **Execute test suite to verify no regressions**: Run the repository test suite using the verified test command to validate the webview integration and input handling logic. (Target: `None`)

## 5. Educational Concepts
### Keyboard Event Default Prevention
- **What is it:** Preventing the browser's default behavior for specific keys like Tab or Enter inside input fields.
- **Why it matters:** Essential for building custom autocomplete and suggestion widgets so that pressing Tab doesn't jump focus or submit forms unintentionally.
- **Connection to Issue:** Fixing the bug requires intercepting `Tab` (and optionally `Enter`) keydown events when the skill suggestion popup is open and calling `event.preventDefault()`.

### VSCode Webview Message Bridge
- **What is it:** The communication channel between the VSCode extension host and the embedded React/web frontend.
- **Why it matters:** Enables UI components inside the webview to interact with extension commands and workspace APIs.
- **Connection to Issue:** Understanding how input events are captured within the webview UI components helps pinpoint where keyboard listeners are attached.

