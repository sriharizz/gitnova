# Issue Context Dossier: `MoonshotAI/kimi-code` #3107

**Title:** fix(acp-server): surface provider errors on session/prompt  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When LLM provider errors (such as 4xx/5xx/rate-limits/connection errors) occur during an ACP session prompt or turn, the ACP server silently resolves the turn with a successful stopReason ('end_turn') instead of propagating a JSON-RPC error. This issue proposes surfacing these provider errors properly as JSON-RPC internal errors via a new `isProviderError` helper.

## 2. Root Cause Analysis
> The error classification logic in `packages/acp-server/src/session.ts` and `packages/acp-server/src/events-map.ts` exclusively checks for authentication errors (`isAuthError`) and maps everything else through `turnEndReasonToStopReason`. The underlying engine correctly tags errors with codes like `provider.api_error`, but the ACP layer discards this differentiation.

## 3. Grounded Code Locations & Citations
- File: `packages/acp-server/src/session.ts` (Lines: `106-145`) | Symbol: `mapPromptLaunchError` | Role: *Prompt launch error mapping function* (Verified: True)
- File: `packages/acp-server/src/events-map.ts` (Lines: `71-110`) | Symbol: `isAuthError` | Role: *Existing auth error helper function* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect existing error classification helpers**: Inspect symbol isAuthError in packages/acp-server/src/events-map.ts and mapPromptLaunchError in packages/acp-server/src/session.ts to understand how errors are currently categorized. (Target: `packages/acp-server/src/events-map.ts`)
2. **Implement isProviderError helper**: Add an isProviderError helper function in packages/acp-server/src/events-map.ts to detect recognized provider error codes such as provider.api_error, rate limits, and connection errors. (Target: `packages/acp-server/src/events-map.ts`)
3. **Update turn end and prompt launch error handling**: Modify onTurnEnded and mapPromptLaunchError in packages/acp-server/src/session.ts to check for provider errors using the new helper and reject the driver with a structured JSON-RPC internal error instead of falling back to end_turn. (Target: `packages/acp-server/src/session.ts`)
4. **Add regression test for provider error propagation**: Add unit tests in packages/acp-server/test/convert.test.ts (or session test suite) verifying that provider errors are correctly propagated as JSON-RPC internal errors. (Target: `packages/acp-server/test/convert.test.ts`)
5. **Run test suite**: Run the repository test command to verify all tests pass successfully without regressions. (Target: `None`)

## 5. Educational Concepts
### JSON-RPC Error Propagation
- **What is it:** Translating internal application or provider failures into standardized remote procedure call error responses.
- **Why it matters:** Ensures that clients calling remote APIs are explicitly notified of failures rather than receiving misleading success responses.
- **Connection to Issue:** Fixes the silent resolution of provider failures so that API clients receive proper JSON-RPC error codes instead of a false 'end_turn' success signal.

### Error Classification & Mapping
- **What is it:** Categorizing error codes from lower layers to handle specific failure modes differently at the application boundary.
- **Why it matters:** Allows servers to adapt generic engine failures into specific client-facing protocols like authentication requests or internal error reporting.
- **Connection to Issue:** Introduces `isProviderError` alongside `isAuthError` to properly route provider-specific error codes to JSON-RPC rejections.

