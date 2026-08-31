# Issue Context Dossier: `fullsend-ai/fullsend` #6463

**Title:** Validate matrix field formats in reusable-dispatch pre-computed matrix path  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Issue #6463 reports that inputs.matrix fields passed to reusable-dispatch.yml via the pre-computed matrix path are currently used without format validation, leaving downstream actions and env vars vulnerable to malicious or malformed input injection.

## 2. Root Cause Analysis
> While normal dispatch paths validate stage names and inputs using explicit regex patterns, the pre-computed matrix path lacks equivalent validation routines when parsing inputs from fromJSON().

## 3. Grounded Code Locations & Citations
- File: `internal/mintcore/claims.go` (Lines: `141-180`) | Symbol: `ValidateWorkflowRef` | Role: *Relevant Code* (Verified: True)
- File: `internal/dispatch/router.go` (Lines: `1-40`) | Symbol: `HarnessRouter` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect ValidateWorkflowRef and HarnessRouter control flows**: Inspect ValidateWorkflowRef in internal/mintcore/claims.go and HarnessRouter in internal/dispatch/router.go to understand how matrix inputs are currently accepted without format validation. (Target: `internal/mintcore/claims.go`)
2. **Implement regex validation for pre-computed matrix fields**: Add strict validation regex patterns for matrix fields (such as agent, role, and source_repo) in internal/mintcore/claims.go to reject malformed or potentially malicious input strings. (Target: `internal/mintcore/claims.go`)
3. **Integrate matrix validation checks into HarnessRouter**: Update internal/dispatch/router.go to invoke the new matrix validation routines when parsing and processing pre-computed matrix inputs. (Target: `internal/dispatch/router.go`)
4. **Add regression tests and verify with test suite**: Add test cases in internal/mintcore/claims_test.go and internal/dispatch/router_test.go verifying that invalid matrix field formats are correctly rejected, then execute the test suite. (Target: `internal/mintcore/claims_test.go`)

## 5. Educational Concepts
### Input Validation & Sanitization
- **What is it:** The process of checking untrusted input data against an expected format, type, or regex before using it in commands, file paths, or execution steps.
- **Why it matters:** Without input validation, external or malformed parameters can manipulate workflow execution, inject malicious payloads, or cause cryptic runtime failures.
- **Connection to Issue:** Directly relates to adding format validation checks on matrix fields like agent, role, and source_repo before they flow into checkout actions and env vars.

### Defensive Programming
- **What is it:** A coding practice where software is designed to anticipate and gracefully handle invalid, unexpected, or malicious states.
- **Why it matters:** It ensures that bugs and security vulnerabilities are caught early through clear validation errors rather than cascading into downstream failures.
- **Connection to Issue:** The issue highlights that normal dispatch paths already enforce regex validation, and defensive checks need to be extended to the pre-computed matrix path.

