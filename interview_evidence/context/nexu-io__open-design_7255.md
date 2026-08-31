# Issue Context Dossier: `nexu-io/open-design` #7255

**Title:** Allow operators to disable Codex workspace-write network access  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Allow operators to disable Codex workspace-write network access via a new environment variable OD_CODEX_NETWORK_ACCESS=false without changing default behavior or touch UI/API layers.

## 2. Root Cause Analysis
> The Codex adapter currently passes hardcoded CLI configuration overrides to subprocess executions of Codex without checking an environment variable flag like OD_CODEX_NETWORK_ACCESS.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/codex-cli.ts` (Lines: `35-55`) | Symbol: `installCodexMcp` | Role: *Codex CLI interaction and runner configuration* (Verified: True)
- File: `apps/daemon/src/connectionTest.ts` (Lines: `806-845`) | Symbol: `stripCodexBinOverride` | Role: *Codex configuration helpers and path overrides* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Codex CLI Adapter Arguments**: Inspect symbol installCodexMcp in apps/daemon/src/codex-cli.ts and verify where hardcoded sandbox_workspace_write.network_access=true CLI arguments are constructed. (Target: `apps/daemon/src/codex-cli.ts`)
2. **Implement OD_CODEX_NETWORK_ACCESS Environment Variable Check**: Update apps/daemon/src/codex-cli.ts to read process.env.OD_CODEX_NETWORK_ACCESS, defaulting to 'true' if unset or invalid, and dynamically assign the network_access configuration flag string ('true' or 'false'). (Target: `apps/daemon/src/codex-cli.ts`)
3. **Add Unit and Integration Tests for Network Access Flag**: Add regression tests in apps/daemon/src/connectionTest.ts or a corresponding test suite verifying that setting OD_CODEX_NETWORK_ACCESS=false correctly propagates sandbox_workspace_write.network_access=false while omitting it preserves true. (Target: `apps/daemon/src/connectionTest.ts`)
4. **Execute Test Suite**: Run the daemon test suite to verify that all existing tests pass and the new network access behavior works as intended. (Target: `None`)

## 5. Educational Concepts
### CLI Configuration Overrides
- **What is it:** Command-line flags or config overrides passed to spawned subprocesses that take precedence over user or project config files.
- **Why it matters:** Understanding how configuration overrides flow from environment variables to subprocess arguments allows operators to control runtime behavior securely.
- **Connection to Issue:** The issue requires checking an environment variable (`OD_CODEX_NETWORK_ACCESS`) to conditionally alter the configuration override passed to the Codex CLI.

### Environment Variable Opt-Outs
- **What is it:** A configuration pattern where a default behavior is active unless an explicit environment variable is set to opt out.
- **Why it matters:** Allows zero-downtime deployment customization across different environments without modifying persistent configuration files.
- **Connection to Issue:** Unset or unknown values preserve the default network-enabled behavior, while exact `false` emits `sandbox_workspace_write.network_access=false`.

