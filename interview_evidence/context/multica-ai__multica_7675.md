# Issue Context Dossier: `multica-ai/multica` #7675

**Title:** [Bug]: Run copilot in schedule task with webhook failed sometimes  
**Repository:** https://github.com/multica-ai/multica  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Running the Copilot agent in a scheduled task triggered by a webhook fails with an error indicating an invalid command format due to unquoted prompts, whereas manual task execution succeeds.

## 2. Root Cause Analysis
> Webhook-triggered task executions build command-line arguments or pass payloads differently than manual triggers, resulting in space-separated words of the prompt being treated as separate command arguments instead of a single quoted string.

## 3. Grounded Code Locations & Citations
- File: `server/internal/analytics/events.go` (Lines: `701-740`) | Symbol: `AutopilotCreated` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect webhook-triggered command construction**: Inspect the AutopilotCreated event handling and webhook execution logic in server/internal/analytics/events.go to locate where command arguments and prompts are assembled. (Target: `server/internal/analytics/events.go`)
2. **Fix unquoted prompt string formatting**: Ensure the prompt argument passed to the Copilot agent during webhook-triggered tasks is properly wrapped in quotes or structured as a single command-line argument to prevent shell parsing errors. (Target: `server/internal/analytics/events.go`)
3. **Add regression test for webhook task execution**: Update server/internal/analytics/events_test.go to add a test case verifying that webhook-triggered task execution correctly formats the prompt argument without invalid command format errors. (Target: `server/internal/analytics/events_test.go`)
4. **Run test suite for verification**: Run the repository test command to verify that all unit and integration tests pass successfully with the fix applied. (Target: `None`)

## 5. Educational Concepts
### Command Argument Splitting
- **What is it:** When spawning external CLI processes, arguments containing spaces must be passed as single parameters rather than split into individual words.
- **Why it matters:** Failing to encapsulate prompts or text strings in quotes causes CLI parsers to interpret individual words as separate flags or positional arguments.
- **Connection to Issue:** Webhook triggers pass prompt strings that get split into separate arguments when invoking the Copilot CLI, causing it to reject the unquoted format.

### Trigger Source Context Handling
- **What is it:** Differentiating execution behavior based on whether a task was triggered manually, via schedule, or through a webhook.
- **Why it matters:** Different trigger sources often inject distinct payload structures or environment contexts that code paths must handle uniformly.
- **Connection to Issue:** The bug specifically manifests in webhook and scheduled task execution paths, highlighting a divergence in how task arguments are constructed compared to manual runs.

