# Issue Context Dossier: `babalae/better-genshin-impact` #3539

**Title:** [bug] 派蒙检测的关闭选项在“独立任务”内的战斗配置中无法生效  
**Repository:** https://github.com/babalae/better-genshin-impact  
**Language:** C#  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The newly added Paimon detection feature is enabled by default, preventing automated combat completion when needed. While users can disable Paimon detection in individual configuration group settings, disabling it within the 'Solo Task' (独立任务) combat configuration settings fails to take effect.

## 2. Root Cause Analysis
> The solo task pathing or combat configuration settings fail to propagate or synchronize the Paimon detection toggle state down to the active runtime task execution context or global configuration handler.

## 3. Grounded Code Locations & Citations
- File: `BetterGenshinImpact/Core/Config/PathingPartyConfig.cs` (Lines: `1-145`) | Symbol: `PathingPartyConfig` | Role: *Pathing party configuration storing solo task combat settings where Paimon detection option might be missing or unlinked.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Paimon detection configuration mapping in PathingPartyConfig.cs**: Inspect PathingPartyConfig.cs to verify how solo task combat settings handle Paimon detection options and identify missing synchronization properties. (Target: `BetterGenshinImpact/Core/Config/PathingPartyConfig.cs`)
2. **Add or link the Paimon detection toggle property**: Expose and bind the Paimon detection boolean property within the solo task configuration context so that UI/config toggles properly serialize and propagate. (Target: `BetterGenshinImpact/Core/Config/PathingPartyConfig.cs`)
3. **Propagate the Paimon detection configuration to runtime execution**: Ensure the runtime task execution context correctly reads the Paimon detection setting from PathingPartyConfig during solo task initialization. (Target: `BetterGenshinImpact/Core/Config/PathingPartyConfig.cs`)
4. **Implement regression test and verify behavior**: Add a unit or integration test verifying that setting Paimon detection to false in PathingPartyConfig successfully disables the runtime feature, then run the test suite. (Target: `None`)

## 5. Educational Concepts
### Configuration Data Binding & Propagation
- **What is it:** The mechanism of mapping UI options and task-specific settings to persistent configuration classes and passing them down to execution logic.
- **Why it matters:** If a configuration property is added to one view or config class (like group-level settings) but not properly propagated or included in alternative task execution configs (like solo tasks), user preferences will be silently ignored.
- **Connection to Issue:** The Paimon detection disable option exists in individual configuration groups but is missing or disconnected in the 'Solo Task' combat configuration flow.

### Observable Properties in CommunityToolkit.Mvvm
- **What is it:** A code-generation feature in C# using source generators to automatically create public properties from private annotated fields.
- **Why it matters:** Understanding how properties are declared with [ObservableProperty] ensures that state changes are correctly recognized and persisted across different configuration scopes.
- **Connection to Issue:** Settings such as pathing and combat configurations rely on these properties to serialize and pass user preferences at runtime.

