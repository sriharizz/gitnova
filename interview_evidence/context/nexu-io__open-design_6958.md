# Issue Context Dossier: `nexu-io/open-design` #6958

**Title:** `od lint` is missing (dual-track gap), and displayed figures have no provenance contract  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The `od lint` command is missing from the CLI, violating the project's dual-track capability exposure rule where features must be accessible via both the web UI/API and the `od` CLI. Additionally, the existing linter lacks provenance checking for figures and numbers in rendered artifacts.

## 2. Root Cause Analysis
> While the daemon API endpoint and server-side logic were built, the corresponding CLI subcommand implementation in `apps/daemon/src/cli.ts` was not wired up or exposed to external agents.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/cli.ts` (Lines: `736-775`) | Symbol: `runLint` | Role: *CLI Lint Execution and Flag Parsing* (Verified: True)
- File: `apps/daemon/src/cli.ts` (Lines: `701-740`) | Symbol: `printLintHelp` | Role: *CLI Help and Usage Documentation for Lint* (Verified: True)
- File: `apps/daemon/src/handoff-cli.ts` (Lines: `1-40`) | Symbol: `isHandoffResponse` | Role: *Reference pattern for modular standalone CLI subcommand implementation* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect CLI Entrypoint and Existing Subcommands**: Examine apps/daemon/src/cli.ts to understand how existing subcommands like export or project handoff parse arguments, handle flags, and communicate with the daemon API. (Target: `apps/daemon/src/cli.ts`)
2. **Implement CLI Lint Help Function**: Implement printLintHelp in apps/daemon/src/cli.ts to display usage documentation, available flags like --fail-on and --json, and target file arguments. (Target: `apps/daemon/src/cli.ts`)
3. **Implement CLI Lint Execution Logic**: Implement runLint in apps/daemon/src/cli.ts to handle file input or stdin, dispatch the request to the POST /api/artifacts/lint daemon endpoint, and properly format the JSON or text output. (Target: `apps/daemon/src/cli.ts`)
4. **Add Regression Test and Run Verification**: Add integration or unit tests covering the new `od lint` CLI subcommand and execute the test suite to verify correct behavior. (Target: `apps/daemon/src/cli.ts`)

## 5. Educational Concepts
### Dual-Track Capability Exposure
- **What is it:** Every feature exposed in the UI or API must also be accessible via the `od` CLI.
- **Why it matters:** Ensures external autonomous agents and headless scripts can compose and execute all system capabilities without relying on a graphical browser.
- **Connection to Issue:** The issue addresses the gap where the linter endpoint exists on the server but has no corresponding `od lint` command.

### CLI Flag Parsing and Result Envelopes
- **What is it:** Standardized command-line argument parsing and JSON output structures for automated tooling.
- **Why it matters:** Enables robust scripting, fail-fast behavior, and structured data exchange between agents and command-line tools.
- **Connection to Issue:** The new `od lint` subcommand needs to parse flags like `--fail-on` and `--json` to match existing CLI commands.

