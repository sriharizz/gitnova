# Issue Context Dossier: `openai/codex` #39906

**Title:** Feature request: add a SkillInvocation hook event  
**Repository:** https://github.com/openai/codex  
**Language:** Rust  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> This issue proposes adding a new 'SkillInvocation' hook event to Codex hooks (`[features] hooks = true`). Currently, tool calls, prompts, and session lifecycle events notify external hook handlers, but explicit and implicit skill activations remain invisible to external handlers.

## 2. Root Cause Analysis
> Hook dispatching currently handles events like user prompt submission or tool calls, but lacks an emission site and hook runtime plumbing for `HookEventName::SkillInvocation` alongside the existing analytics and OTEL emission sites in `skills.rs`.

## 3. Grounded Code Locations & Citations
- File: `codex-rs/analytics/src/client.rs` (Lines: `281-305`) | Symbol: `track_skill_invocations` | Role: *Existing analytics tracking method for skill invocations* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Skill Invocation Control Flow**: Examine how track_skill_invocations is called within codex-rs/analytics/src/client.rs and related skill handling files to identify where skill invocation events are triggered. (Target: `codex-rs/analytics/src/client.rs`)
2. **Define HookEventName::SkillInvocation**: Add the new SkillInvocation variant to the hook event enumeration in the hooks module, ensuring it includes metadata such as skill name, file path, scope, invocation type, turn ID, and session ID. (Target: `codex-rs/hooks/src/lib.rs`)
3. **Wire Skill Invocation Dispatcher**: Integrate the hook dispatch call alongside track_skill_invocations whenever a skill is explicitly or implicitly invoked in the skill execution runtime. (Target: `codex-rs/core/src/skills.rs`)
4. **Add Regression Test**: Implement a unit test verifying that invoking a skill successfully dispatches the SkillInvocation hook event with the expected payload to external hook handlers. (Target: `codex-rs/hooks/src/tests.rs`)
5. **Run Test Suite**: Execute cargo test to verify that the new SkillInvocation hook event passes all test assertions without breaking existing telemetry or hook mechanisms. (Target: `None`)

## 5. Educational Concepts
### Hook Event Dispatching
- **What is it:** The mechanism by which internal system events are serialized and dispatched to external hook handlers.
- **Why it matters:** Understanding how events flow from core subsystems to external handlers allows developers to expose new telemetry and audit points safely.
- **Connection to Issue:** Fixing this issue requires adding a new `SkillInvocation` hook event that mirrors existing hook dispatch patterns.

### Event Telemetry vs Hook Notifications
- **What is it:** Internal analytics tracking records usage metrics, whereas external hooks notify user-configured external scripts and handlers.
- **Why it matters:** Separating internal analytics from user hooks ensures telemetry stays private while giving users audit capability.
- **Connection to Issue:** Skill invocations are already tracked via analytics; this feature extends them to the hook runtime so external handlers receive them too.

