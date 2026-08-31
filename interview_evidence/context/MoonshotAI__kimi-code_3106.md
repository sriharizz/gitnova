# Issue Context Dossier: `MoonshotAI/kimi-code` #3106

**Title:** fix(acp-server): include full bash command in permission requests  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The ACP session/request_permission for a Bash tool call currently truncates the command to the first 50 characters in the approval prompt's content list because displayBlockToAcpContent lacks a handler for command display blocks. This fix adds a handler to include the full bash command on the ACP wire.

## 2. Root Cause Analysis
> The AgentPermissionGate raises an approval request containing a display object with `kind: 'command'` and the full `command` property. When buildPermissionToolCallUpdate calls `displayBlockToAcpContent(req.display)`, the conversion function in `packages/acp-server/src/convert.ts` (or `packages/acp-adapter/src/convert.ts`) falls through all existing conditions (`diff`, `file_io`, `plan_review`) and returns `null`, dropping the command details.

## 3. Grounded Code Locations & Citations
- File: `packages/acp-server/src/approval.ts` (Lines: `246-285`) | Symbol: `buildPermissionToolCallUpdate` | Role: *Builds the permission tool call update including the headline entry from displayBlockToAcpContent.* (Verified: True)
- File: `packages/acp-server/src/convert.ts` (Lines: `281-320`) | Symbol: `displayBlockToAcpContent` | Role: *Converts tool input display blocks into ACP content entries; currently missing a handler for `kind: 'command'`.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect displayBlockToAcpContent in convert.ts**: Inspect symbol displayBlockToAcpContent in packages/acp-server/src/convert.ts to identify how different display block kinds (such as diff, file_io, plan_review) are processed and where the missing 'command' kind handler should be added. (Target: `packages/acp-server/src/convert.ts`)
2. **Implement command block handler in displayBlockToAcpContent**: Update displayBlockToAcpContent in packages/acp-server/src/convert.ts to handle blocks with kind 'command' by mapping block.command into a ToolCallContent text entry so the full command is sent across the ACP wire. (Target: `packages/acp-server/src/convert.ts`)
3. **Verify buildPermissionToolCallUpdate integration in approval.ts**: Examine packages/acp-server/src/approval.ts around buildPermissionToolCallUpdate to ensure that the updated content list properly incorporates the new command block content without truncation. (Target: `packages/acp-server/src/approval.ts`)
4. **Add unit and integration tests for command display blocks**: Update packages/acp-server/test/convert.test.ts and approval.test.ts to verify that display blocks with kind 'command' correctly generate the expected ToolCallContent text representation without 50-character truncation. (Target: `packages/acp-server/test/convert.test.ts`)
5. **Run test suite to verify the fix**: Execute the test command to ensure all ACP server conversion and approval tests pass successfully and no regressions are introduced. (Target: `None`)

## 5. Educational Concepts
### ACP Wire Protocol Mapping
- **What is it:** Translating internal agent core representations into standardized Agent Client Protocol (ACP) wire messages.
- **Why it matters:** Understanding how internal data structures map to wire protocol objects ensures that external IDE clients like JetBrains or Zed receive all necessary context to render UI components correctly.
- **Connection to Issue:** Fixing this issue requires mapping internal tool input display blocks of `kind: 'command'` into valid ACP text content entries so the full command is sent across the wire.

### Pure Conversion Functions
- **What is it:** Functions that take input data structures and return transformed outputs without performing side effects or I/O operations.
- **Why it matters:** Pure functions make business logic and protocol mappers exceptionally easy to unit test in isolation without setting up live servers or mock connections.
- **Connection to Issue:** displayBlockToAcpContent is a pure conversion function whose logic can be extended and thoroughly tested with straightforward unit test fixtures.

