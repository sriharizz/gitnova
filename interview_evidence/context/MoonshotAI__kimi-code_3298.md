# Issue Context Dossier: `MoonshotAI/kimi-code` #3298

**Title:** [Web UI] A single Ctrl+V image paste creates two attachment chips (clipboard.png + image.png)  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> In the Kimi-code Web UI, pressing Ctrl+V once to paste a screenshot results in two attachment chips (`clipboard.png` and `image.png`) being created, indicating that multiple handlers (such as a paste event and a clipboard poll) are triggering on the same clipboard item.

## 2. Root Cause Analysis
> Two distinct event or polling handlers in the web interface independently detect and process the clipboard contents upon a single paste action, resulting in dual file creation without proper deduplication or event prevention.

## 3. Grounded Code Locations & Citations
- File: `apps/vscode/src/KimiWebviewProvider.ts` (Lines: `1-40`) | Symbol: `KimiWebviewProvider` | Role: *Webview container managing extension bridge and UI communication* (Verified: True)
- File: `apps/vscode/src/bridge-handler.ts` (Lines: `1-30`) | Symbol: `BridgeHandler` | Role: *Bridge handler coordinating messages between webview and backend runtime* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect clipboard paste event handling**: Inspect KimiWebviewProvider in apps/vscode/src/KimiWebviewProvider.ts and BridgeHandler in apps/vscode/src/bridge-handler.ts to locate where paste events and clipboard items are processed. (Target: `apps/vscode/src/KimiWebviewProvider.ts`)
2. **Deduplicate clipboard processing**: Modify the paste event listener or bridge message handler in apps/vscode/src/bridge-handler.ts to check if an identical clipboard image has already been handled or queued within a short time window. (Target: `apps/vscode/src/bridge-handler.ts`)
3. **Prevent default or stop propagation**: Ensure event propagation is correctly handled and default actions are appropriately prevented in KimiWebviewProvider when processing clipboard paste events to avoid double-firing. (Target: `apps/vscode/src/KimiWebviewProvider.ts`)
4. **Execute test suite for verification**: Run the test suite using the verified test command to verify that single paste actions result in exactly one attachment chip without breaking existing behavior. (Target: `None`)

## 5. Educational Concepts
### Event Handling and Prevention
- **What is it:** Managing browser DOM events so that user actions do not trigger multiple redundant handlers.
- **Why it matters:** Failing to stop propagation or handle duplicate triggers leads to redundant state mutations and duplicate UI elements.
- **Connection to Issue:** Fixing the duplicate paste issue requires ensuring that paste events and clipboard polling mechanisms do not both process the exact same clipboard item simultaneously.

### Clipboard API Interaction
- **What is it:** Accessing and reading image or text payloads from the system clipboard securely via browser APIs.
- **Why it matters:** Properly handling clipboard data streams prevents unexpected binary files or incorrect filenames from populating user inputs.
- **Connection to Issue:** Helps distinguish between `clipboard.png` and `image.png` sources to unify or filter redundant capture paths.

