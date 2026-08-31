# Issue Context Dossier: `zitadel/oidc` #961

**Title:** Preserve infrastructure errors in rp helpers  
**Repository:** https://github.com/zitadel/oidc  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Higher-level relying party (rp) helper functions currently convert low-level networking or infrastructure errors (such as timeouts, connection refusals, and DNS resolution failures) directly into generic unauthorized or error handlers, stripping away the underlying Go error chain. This prevents consumers from inspecting network or infrastructure failures using standard Go mechanisms like `errors.Is` and `errors.As`.

## 2. Root Cause Analysis
> Functions in packages like `rp` or client helpers invoke `client.Do` or HTTP helpers which return underlying network or protocol errors, but higher-level wrapper functions intercept these failures and treat them as authentication/unauthorized errors or discard the wrapped error context.

## 3. Grounded Code Locations & Citations
- File: `pkg/client/rp/relying_party.go` (Lines: `911-933`) | Symbol: `unauthorizedError` | Role: *Relevant Code* (Verified: True)
- File: `pkg/client/client.go` (Lines: `176-215`) | Symbol: `CallTokenExchangeEndpoint` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect error handling in relying party and client endpoints**: Examine unauthorizedError in pkg/client/rp/relying_party.go and CallTokenExchangeEndpoint in pkg/client/client.go to identify where low-level network and infrastructure errors are swallowed or inappropriately wrapped into generic authentication errors. (Target: `pkg/client/rp/relying_party.go`)
2. **Preserve Go error wrapping for network failures**: Modify the HTTP response and error handling logic in pkg/client/rp/relying_party.go and pkg/client/client.go to wrap underlying transport or timeout errors using Go 1.13+ fmt.Errorf with %w instead of discarding the error chain. (Target: `pkg/client/client.go`)
3. **Add regression test covering error unwrapping**: Add a new unit test in pkg/client/rp/relying_party_test.go or pkg/client/integration_test.go that simulates a network timeout or connection refusal and verifies that errors.Is or errors.As can successfully inspect the underlying error. (Target: `pkg/client/rp/relying_party_test.go`)
4. **Run test suite to verify fix**: Run the package tests using go test to confirm that all existing functionality passes and the new regression test successfully validates error unwrapping. (Target: `None`)

## 5. Educational Concepts
### Go Error Wrapping and Inspection
- **What is it:** Go 1.13 introduced built-in support for wrapping errors using fmt.Errorf with the %w verb, and inspecting them using errors.Is and errors.As.
- **Why it matters:** It allows calling code to distinguish between different failure modes (such as a timeout versus an invalid credential) programmatically rather than string-matching.
- **Connection to Issue:** Fixing this issue requires ensuring that low-level infrastructure errors are properly wrapped or preserved so consumers can use errors.Is and errors.As on them.

### Separation of Infrastructure and Authentication Failures
- **What is it:** Network/infrastructure failures (like DNS errors or timeouts) are distinct operational events from authentication failures (like invalid client secrets or unauthorized tokens).
- **Why it matters:** Treating an unreachable server as an unauthorized user misleads administrators and clients about the root cause of a request failure.
- **Connection to Issue:** The issue requests that rp helpers stop masking infrastructure failures as unauthorized errors.

