# Issue Context Dossier: `kestra-io/kestra` #18477

**Title:** [Bash2.0] Schedule trigger defaults to the server timezone, not UTC as documented  
**Repository:** https://github.com/kestra-io/kestra  
**Language:** Java  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The Schedule trigger documentation states that the default timezone is UTC if none is explicitly specified. However, at runtime, schedules without a timezone default to the server's local timezone (`ZoneId.systemDefault()`), causing discrepancies across servers in different time zones.

## 2. Root Cause Analysis
> Cron evaluation and trigger instantiation fall back to the system default timezone instead of explicitly enforcing UTC when the timezone field is omitted or unassigned in the trigger configuration.

## 3. Grounded Code Locations & Citations
- File: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java` (Lines: `561-600`) | Symbol: `TriggerEventHandler` | Role: *Handles trigger event creation and next evaluation date calculations* (Verified: True)
- File: `scheduler/src/main/java/io/kestra/scheduler/DefaultScheduler.java` (Lines: `246-285`) | Symbol: `DefaultScheduler` | Role: *Manages scheduler loops and trigger event consumers* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect TriggerEventHandler timezone fallback**: Inspect TriggerEventHandler in scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java to identify where trigger timezone resolution defaults to ZoneId.systemDefault() or unassigned values. (Target: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java`)
2. **Update timezone default to UTC**: Modify the schedule trigger evaluation logic in TriggerEventHandler.java so that when the timezone property is null or omitted, it explicitly falls back to ZoneId.of("UTC") instead of ZoneId.systemDefault(). (Target: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java`)
3. **Inspect DefaultScheduler integration**: Verify DefaultScheduler in scheduler/src/main/java/io/kestra/scheduler/DefaultScheduler.java to ensure it correctly respects the UTC timezone fallback handled by TriggerEventHandler. (Target: `scheduler/src/main/java/io/kestra/scheduler/DefaultScheduler.java`)
4. **Add regression test and execute verification suite**: Add a unit or integration test verifying that a Schedule trigger created without an explicit timezone correctly evaluates next execution dates using UTC regardless of the host system timezone, then execute the test command. (Target: `scheduler/src/test/java/io/kestra/scheduler/TriggerEventHandlerTest.java`)

## 5. Educational Concepts
### Timezone Handling in Cron Triggers
- **What is it:** Timezones determine how cron expressions (like '0 3 * * *') are interpreted relative to global UTC time.
- **Why it matters:** Failing to normalize or explicitly default to UTC leads to environment-dependent execution times, causing bugs when workflows run on servers with different local timezones.
- **Connection to Issue:** The issue stems from cron scheduling defaulting to the local server timezone instead of UTC, violating user documentation.

### Trigger Event State Management
- **What is it:** Kestra manages trigger lifecycle states (such as next evaluation dates) via event handlers and state stores.
- **Why it matters:** Understanding how triggers are initialized and evaluated helps developers trace where default values like timezones are applied during schedule evaluation.
- **Connection to Issue:** Fixing the default timezone requires ensuring that triggers without an explicit timezone property correctly resolve to UTC during evaluation date computations.

