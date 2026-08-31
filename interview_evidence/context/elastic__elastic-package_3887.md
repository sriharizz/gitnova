# Issue Context Dossier: `elastic/elastic-package` #3887

**Title:** Kibana client never retries connection-level errors: `checkRetry` treats every `*url.Error` as unrecoverable  
**Repository:** https://github.com/elastic/elastic-package  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The Kibana client's custom HTTP retry logic incorrectly treats all `*url.Error` types as unrecoverable. Because Go's `net/http` package wraps every request error in `*url.Error`, transient transport errors like EOF or connection resets are mistakenly blocked from retrying.

## 2. Root Cause Analysis
> In `internal/retry/http.go`, the check for `*url.Error` matches unconditionally and returns `false` without checking the inner error. As a result, the subsequent fallback branches for retrying general errors and TLS-specific checks are dead code for anything returned by `http.Client.Do`.

## 3. Grounded Code Locations & Citations
- File: `internal/kibana/client.go` (Lines: `211-250`) | Symbol: `Client.newHttpClient` | Role: *Configures and wraps the HTTP client with retry logic.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect HTTP retry check logic**: Examine the `checkRetry` function within `internal/retry/http.go` to understand how `*url.Error` is currently intercepted and causes immediate return without evaluating underlying transport errors. (Target: `internal/retry/http.go`)
2. **Refine url.Error unwrapping in checkRetry**: Modify the `*url.Error` handling in `internal/retry/http.go` so that if an error is a `*url.Error`, the underlying `Err` field is inspected. Allow transient network errors (like EOF or connection reset) wrapped inside `url.Error` to fall through to retry evaluation, while properly handling unrecoverable errors. (Target: `internal/retry/http.go`)
3. **Add regression test for transient url.Error retries**: In `internal/kibana/client_test.go`, add a unit test that simulates a transient transport error wrapped in a `*url.Error` (such as an EOF during request execution) and verifies that the HTTP client retry mechanism successfully retries the request according to the policy. (Target: `internal/kibana/client_test.go`)
4. **Run unit tests to verify fix**: Run the test suite focusing on the Kibana client and retry packages to ensure all tests pass successfully without regressions. (Target: `internal/kibana/client_test.go`)

## 5. Educational Concepts
### HTTP Request Retries & Transient Errors
- **What is it:** Automatic re-execution of failed HTTP requests when temporary network failures occur.
- **Why it matters:** In distributed test environments, services can occasionally drop idle connections or experience brief network blips. Retries prevent these harmless transient glitches from causing system test failures.
- **Connection to Issue:** The custom retry policy improperly blocks retries on transient connection errors by misidentifying them as fatal URL errors.

### Error Wrapping and Unwrapping in Go
- **What is it:** Go's idiom of wrapping low-level errors inside high-level context errors using verbs like `%w` or standard library wrappers.
- **Why it matters:** Developers need to unwrap errors or use `errors.As` / `errors.Is` properly to inspect root causes rather than matching top-level wrapper types blindly.
- **Connection to Issue:** `http.Client.Do` wraps every error in `*url.Error`, so the retry policy must unwrap the inner error to distinguish between bad URLs and temporary network connection drops.

