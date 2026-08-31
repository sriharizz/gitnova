# Issue Context Dossier: `microcks/microcks` #2226

**Title:** Replace arbitrary delays with deterministic readiness for async tests  
**Repository:** https://github.com/microcks/microcks  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Currently, client libraries testing asynchronous APIs with Microcks must wait for an arbitrary delay (sleep) before publishing messages to ensure the broker consumer is ready. This issue aims to replace this non-deterministic delay with a deterministic polling mechanism by exposing the lifecycle phase of each asynchronous test case (e.g., CONNECTING, WAITING_FOR_MESSAGE, DONE) via the Microcks API.

## 2. Root Cause Analysis
> The root cause is that the TestCaseResult model (defined in webapp/src/main/webapp/src/app/models/test.model.ts and its backend Java equivalent) lacks a field to track the intermediate lifecycle state of the consumer subscription. The async minion does not have a mechanism or API endpoint to report when a broker consumer has successfully connected and is ready to receive messages, forcing clients to rely on arbitrary sleep delays.

## 3. Grounded Code Locations & Citations
- File: `webapp/src/main/webapp/src/app/models/test.model.ts` (Lines: `75-80`) | Symbol: `TestCaseResult` | Role: *Frontend model representing the test case result where the new phase field and TestCasePhase enum must be added.* (Verified: True)
- File: `webapp/src/main/webapp/src/app/services/tests.service.ts` (Lines: `36-66`) | Symbol: `TestsService` | Role: *Frontend service that retrieves test results from the backend API.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Frontend Models and Services**: Inspect `webapp/src/main/webapp/src/app/models/test.model.ts` to locate the `TestCaseResult` interface/class, and check `webapp/src/main/webapp/src/app/services/tests.service.ts` to see how test results are fetched and handled. (Target: `webapp/src/main/webapp/src/app/models/test.model.ts`)
2. **Define TestCasePhase Enum and Update TestCaseResult**: Define a new `TestCasePhase` enum with values `CONNECTING`, `WAITING_FOR_MESSAGE`, and `DONE` in `webapp/src/main/webapp/src/app/models/test.model.ts`. Add an optional `phase` field of type `TestCasePhase` to the `TestCaseResult` model. (Target: `webapp/src/main/webapp/src/app/models/test.model.ts`)
3. **Update Backend Java Models and API Endpoints**: Locate the backend Java equivalent of `TestCaseResult` (typically in the core or domain module) and add the `TestCasePhase` enum and `phase` field. Update the API controller/service responsible for updating and retrieving test case results to allow the async minion to report the phase. (Target: `microcks-core/src/main/java/io/github/microcks/domain/TestCaseResult.java`)
4. **Verify and Test the Changes**: Add integration tests in the testsuite (e.g., `testsuite/api-tests.js`) to verify that the phase transitions correctly from CONNECTING to WAITING_FOR_MESSAGE and finally to DONE, and run the maven build/test command to verify. (Target: `testsuite/api-tests.js`)

## 5. Educational Concepts
### Deterministic Readiness in Asynchronous Testing
- **What is it:** Instead of waiting for an arbitrary amount of time (like a sleep or delay) and hoping a background consumer is ready, deterministic readiness uses explicit state signaling (such as a 'WAITING_FOR_MESSAGE' phase) to notify the test runner exactly when it is safe to proceed.
- **Why it matters:** Using arbitrary delays makes tests flaky, slow, and environment-dependent. Deterministic readiness ensures tests run as fast as possible and eliminates race conditions in CI/CD pipelines.
- **Connection to Issue:** This concept is the core goal of the issue: introducing a TestCasePhase enum to signal when the async minion's broker consumer is ready, allowing clients to publish messages immediately without sleeping.

### Backward-Compatible API Design
- **What is it:** Designing API changes so that newer servers can still communicate with older clients, and newer clients can gracefully fall back when communicating with older servers.
- **Why it matters:** In distributed systems, you cannot upgrade all components (server, minion, client libraries) simultaneously. Backward compatibility prevents system failures during rolling updates.
- **Connection to Issue:** The new phase field must be optional/nullable so that older clients do not break when receiving it, and newer clients must fall back to legacy delays if the server does not return a phase.

