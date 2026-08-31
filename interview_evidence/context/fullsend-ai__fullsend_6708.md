# Issue Context Dossier: `fullsend-ai/fullsend` #6708

**Title:** Add CI check for OPENSHELL_VERSION/SHA consistency in openshell-version.sh  
**Repository:** https://github.com/fullsend-ai/fullsend  
**Language:** Go  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> This issue proposes adding a CI check to validate that OPENSHELL_VERSION and OPENSHELL_SHA in `.github/scripts/openshell-version.sh` are consistent with each other, preventing mismatched tags and commit SHAs from bypassing CI checks when non-Renovate authors modify the file.

## 2. Root Cause Analysis
> The version/SHA coupling in `.github/scripts/openshell-version.sh` relies solely on Renovate's post-upgrade tasks, leaving a gap where manual edits or AI-agent PRs can modify the version string without updating the corresponding tag commit SHA.

## 3. Grounded Code Locations & Citations
- File: `internal/config/config_test.go` (Lines: `1-40`) | Symbol: `TestValidateAgentEntries_LocalPathAcceptedWithoutHash` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect openshell-version.sh and existing workflows**: Examine .github/scripts/openshell-version.sh to understand how OPENSHELL_VERSION and OPENSHELL_SHA are defined and used, and inspect existing workflow configurations to determine the best integration point. (Target: `.github/scripts/openshell-version.sh`)
2. **Implement version and SHA validation logic**: Add a validation script or check that queries the GitHub API or uses git/curl to fetch the official commit SHA for the tag corresponding to OPENSHELL_VERSION and asserts it matches OPENSHELL_SHA. (Target: `.github/scripts/openshell-version.sh`)
3. **Integrate validation step into CI workflows**: Add a workflow step or job in GitHub Actions that executes the consistency check whenever .github/scripts/openshell-version.sh is modified or on every PR. (Target: `.github/workflows/ci.yml`)
4. **Add regression test script or local test harness verification**: Create a test case or local script execution that simulates mismatched OPENSHELL_VERSION and OPENSHELL_SHA values to verify the validation check fails with a clear error message. (Target: `internal/config/config_test.go`)

## 5. Educational Concepts
### CI Pipeline Validation
- **What is it:** Automated checks run on every code push or pull request to verify code correctness and consistency.
- **Why it matters:** Ensures that mechanical mistakes or stale configuration values are caught automatically before merging.
- **Connection to Issue:** Adding a CI check prevents version and commit SHA mismatches from slipping through manual reviews or agent PRs.

### Dependency Pinning and Consistency
- **What is it:** Ensuring external tool versions match their exact immutable commit identifiers.
- **Why it matters:** Guarantees reproducible builds and prevents security drifts or unexpected behavior from mismatched references.
- **Connection to Issue:** The openshell version string must map precisely to the correct repository commit SHA to maintain build integrity.

