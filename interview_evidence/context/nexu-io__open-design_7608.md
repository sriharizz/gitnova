# Issue Context Dossier: `nexu-io/open-design` #7608

**Title:** pi-ai 0.84.3: provider catalog data shipped as JavaScript inside .json files breaks CJS consumers  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The package dependency `@earendil-works/pi-ai@0.84.3` incorrectly ships JavaScript module code inside files ending with a `.json` extension. When plain CommonJS (CJS) Node.js require chains attempt to load these catalog files, Node runs `JSON.parse` on them, throwing a `SyntaxError` due to encountering JavaScript statements like `var` and `export`.

## 2. Root Cause Analysis
> In-process ESM or bundler setups (like Vite or `tsx`) transpile or handle these files correctly, but plain Node CJS module resolution strictly enforces `JSON.parse()` for `.json` files. The upstream build or generation script writes JavaScript module code out to files with `.json` extensions instead of serializing pure JSON or assigning `.js` extensions.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/cli.ts` (Lines: `5426-5465`) | Symbol: `publishToMarketplaceJson` | Role: *Illustrates standard JSON file reading and writing practices using `JSON.parse` and `JSON.stringify`.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect dependency loading behavior**: Inspect how `@earendil-works/pi-ai@0.84.3` provider catalog files are loaded in CommonJS contexts and verify where the `SyntaxError` occurs during `JSON.parse` execution. (Target: `apps/daemon/src/connectionTest.ts`)
2. **Review JSON file handling standards**: Review standard JSON file reading and writing practices using `JSON.parse` and `JSON.stringify` to ensure proper parsing expectations. (Target: `apps/daemon/src/cli.ts`)
3. **Implement robust file loading or patching strategy**: Implement a custom loader, patch, or wrapper around the affected `@earendil-works/pi-ai` module files or upstream consumption so that files with JavaScript statements are executed or read appropriately instead of enforcing strict `JSON.parse`. (Target: `None`)
4. **Add regression test for provider catalog loading**: Add a dedicated regression test in apps/daemon/src/connectionTest.ts or equivalent test suite verifying that provider catalog modules from `@earendil-works/pi-ai` load successfully without throwing a `SyntaxError`. (Target: `apps/daemon/src/connectionTest.ts`)
5. **Run test suite for verification**: Run the repository test command to verify that all modules load correctly and no `SyntaxError` occurs during CJS require chains. (Target: `None`)

## 5. Educational Concepts
### CommonJS vs ESM Module Resolution in Node.js
- **What is it:** Node.js handles CommonJS (`require`) and ES Modules (`import`) differently, including how file extensions are mapped to specific internal module loaders.
- **Why it matters:** Developers need to know that file extensions dictate how Node.js parses and executes files at runtime.
- **Connection to Issue:** The issue stems from Node's CJS loader rigidly assuming any `.json` file must be parsed via `JSON.parse`, failing when JavaScript syntax is encountered.

### File Extension Semantics and Serialization
- **What is it:** The filename extension (such as `.json`, `.js`, or `.cjs`) acts as a contract telling runtime loaders how to process the file contents.
- **Why it matters:** Mismatched extensions and file contents lead to hard-to-debug runtime syntax errors.
- **Connection to Issue:** The generated provider catalog files contain JavaScript code (`var`, `export`) but are named with `.json` extensions, violating the loader contract.

