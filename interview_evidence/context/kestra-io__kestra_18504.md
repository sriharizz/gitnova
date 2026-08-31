# Issue Context Dossier: `kestra-io/kestra` #18504

**Title:** [Bash2.0] A backfill runs the occurrence at its end date but not at its start date  
**Repository:** https://github.com/kestra-io/kestra  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When a user initiates a backfill range for a scheduled trigger, executions are created for occurrences from the start date plus one tick through the end date, skipping the exact occurrence at the start date.

## 2. Root Cause Analysis
> The root cause stems from how backfill execution loops or schedule evaluations compute or advance the initial trigger iteration window, causing the boundary condition at the exact start timestamp to be bypassed or excluded.

## 3. Grounded Code Locations & Citations
- File: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java` (Lines: `281-320`) | Symbol: `updateForLastMissedSchedule` | Role: *Relevant Code* (Verified: True)
- File: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java` (Lines: `176-215`) | Symbol: `onDeleteBackfillTrigger` | Role: *Relevant Code* (Verified: True)
- File: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java` (Lines: `246-285`) | Symbol: `updateForReEnabledTrigger` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect TriggerEventHandler scheduling logic**: Inspect symbol updateForLastMissedSchedule and related backfill methods in scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java to understand how the backfill start timestamp boundary is evaluated. (Target: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java`)
2. **Adjust backfill start date boundary condition**: Modify the initial tick calculation or iteration range condition within TriggerEventHandler so that occurrences starting exactly at the backfill start date are included rather than skipped. (Target: `scheduler/src/main/java/io/kestra/scheduler/TriggerEventHandler.java`)
3. **Add regression test for backfill start date**: Add a unit or integration test verifying that initiating a backfill range correctly generates an execution for the exact start timestamp occurrence in addition to subsequent ticks. (Target: `scheduler/src/test/java/io/kestra/scheduler/TriggerEventHandlerTest.java`)
4. **Run test suite to verify fix**: Execute the test command to confirm that the backfill range inclusions pass successfully without regressions. (Target: `None`)

## 5. Educational Concepts
### Backfill Date Boundary Handling
- **What is it:** Handling inclusive versus exclusive start and end boundaries when generating historical scheduled occurrences.
- **Why it matters:** Incorrect boundary handling causes users to lose critical executions at the beginning or end of their specified backfill window.
- **Connection to Issue:** Directly explains why the trigger execution at the start date timestamp is omitted while subsequent ones run.

### Trigger Evaluation and Scheduling State
- **What is it:** The mechanism by which Kestra tracks evaluated timestamps and schedules next execution occurrences.
- **Why it matters:** Understanding state progression prevents corrupting running backfills or improperly skipping scheduled ticks.
- **Connection to Issue:** Relates to how TriggerEventHandler manages state updates and re-enabled triggers during backfill operations.

