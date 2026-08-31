# Issue Context Dossier: `babalae/better-genshin-impact` #3524

**Title:** [bug] 更新中途报错却改变版本号  
**Repository:** https://github.com/babalae/better-genshin-impact  
**Language:** C#  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The application updates its version number or marks a new version before the update process has fully completed and verified successfully, causing broken states or failures if the update fails halfway.

## 2. Root Cause Analysis
> When application updates or version checks execute, the state is persisted or advanced immediately upon initiating the process or reading the remote version metadata, rather than waiting for an explicit success confirmation or validation check of the downloaded package.

## 3. Grounded Code Locations & Citations
- File: `BetterGenshinImpact/Core/Config/Global.cs` (Lines: `36-75`) | Symbol: `IsNewVersion` | Role: *Version comparison logic used during update checks* (Verified: True)
- File: `BetterGenshinImpact/Core/Config/CommonConfig.cs` (Lines: `71-107`) | Symbol: `CommonConfig` | Role: *Configuration storage for run state and version tracking* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Version Tracking and Update Logic**: Inspect IsNewVersion in BetterGenshinImpact/Core/Config/Global.cs and configuration storage in BetterGenshinImpact/Core/Config/CommonConfig.cs to understand how version comparison and update state persistence are triggered. (Target: `BetterGenshinImpact/Core/Config/Global.cs`)
2. **Defer Version State Persistence**: Modify the update workflow so that version state changes and configuration updates in CommonConfig are only persisted after download and file integrity verification have successfully completed. (Target: `BetterGenshinImpact/Core/Config/CommonConfig.cs`)
3. **Add Success Validation Guard**: Add explicit error handling and validation checks around the update sequence to prevent premature version advancement if an exception or download failure occurs. (Target: `BetterGenshinImpact/Core/Config/Global.cs`)
4. **Implement Regression Test and Verify**: Add unit tests verifying that simulated update failures do not advance the stored version state, and run dotnet test to validate the changes. (Target: `None`)

## 5. Educational Concepts
### Optimistic State Mutation vs Transactional Confirmation
- **What is it:** Changing application state before an operation actually succeeds.
- **Why it matters:** If an operation fails halfway, saving state prematurely leaves the application in an inconsistent or corrupted state.
- **Connection to Issue:** Changing the stored version number before the update finishes successfully causes subsequent update cycles to fail because the app thinks it is already up to date.

### Post-Condition Validation
- **What is it:** Verifying that all steps of a critical workflow completed without errors before committing the results.
- **Why it matters:** Ensures system reliability and prevents cascading failures caused by partial operations.
- **Connection to Issue:** The issue requests that version updates only occur after successful completion and integrity validation of the update package.

