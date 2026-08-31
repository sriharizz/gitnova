# Issue Context Dossier: `kubescape/kubescape` #3286

**Title:** fix(core): use case-insensitive check for RCE keyword in vulnerability description  
**Repository:** https://github.com/kubescape/kubescape  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Fix a case-sensitivity bug in the vulnerability remote code execution (RCE) detection where `Vulnerability.IsRCE()` checks for the exact uppercase string "RCE" against `v.Description` rather than utilizing the lowercased description string, leading to under-reporting of vulnerabilities.

## 2. Root Cause Analysis
> The keyword check was implemented using the original mixed-case `v.Description` with an uppercase literal "RCE" instead of using the precomputed lowercased `desc` string like other keyword checks in the same context.

## 3. Grounded Code Locations & Citations
- File: `core/cautils/datastructuresmethods.go` (Lines: `1-40`) | Symbol: `IsRCE` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Vulnerability.IsRCE implementation**: Inspect symbol IsRCE in file core/cautils/datastructuresmethods.go and verify how the description string is converted to lowercase and where strings.Contains is used. (Target: `core/cautils/datastructuresmethods.go`)
2. **Fix case-sensitivity in IsRCE check**: Modify strings.Contains(v.Description, "RCE") in core/cautils/datastructuresmethods.go to check against the lowercased desc variable using strings.Contains(desc, "rce"). (Target: `core/cautils/datastructuresmethods.go`)
3. **Add regression tests for case-insensitive RCE detection**: Update core/cautils/datastructuresmethods_test.go to add test cases covering lowercase "rce", mixed-case "Rce", and uppercase "RCE" descriptions. (Target: `core/cautils/datastructuresmethods_test.go`)
4. **Run tests to verify the fix**: Execute the test suite in core/cautils to ensure that all IsRCE test cases pass successfully without regressions. (Target: `core/cautils/datastructuresmethods_test.go`)

## 5. Educational Concepts
### Case-Insensitive Substring Matching
- **What is it:** Ensuring text searches do not fail due to differing capitalization (uppercase vs. lowercase).
- **Why it matters:** Real-world vulnerability descriptions vary wildly in capitalization; failing to account for case leads to missed detections and false negatives.
- **Connection to Issue:** The issue stems from checking for uppercase "RCE" on a mixed-case string instead of utilizing the lowercased description.

### Defensive Variable Reuse
- **What is it:** Reusing pre-processed or sanitized variables throughout a function to maintain consistency and prevent bugs.
- **Why it matters:** When a function transforms an input once (like lowercasing), subsequent checks should use that transformed version to avoid accidental inconsistencies.
- **Connection to Issue:** The function already created a lowercased `desc` variable but failed to use it for the RCE check.

