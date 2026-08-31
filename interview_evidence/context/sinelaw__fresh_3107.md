# Issue Context Dossier: `sinelaw/fresh` #3107

**Title:** Bug: "Tokyo Night" theme listed on homepage but missing  
**Repository:** https://github.com/sinelaw/fresh  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The user reports that the 'Tokyo Night' theme is listed on the homepage (https://getfresh.dev) as a built-in theme, but is missing from the `Select Theme` list after installing fresh-editor v0.4.10, making it unavailable for selection.

## 2. Root Cause Analysis
> The issue stems from a discrepancy between documentation/homepage claims and the actual packaged built-in themes or theme loader configurations in the repository.

## 3. Grounded Code Locations & Citations
- File: `crates/fresh-editor/src/app/editor_init.rs` (Lines: `946-985`) | Symbol: `scan_installed_packages` | Role: *Theme registry initialization and fallback logic* (Verified: True)
- File: `crates/fresh-editor/src/config.rs` (Lines: `8926-8965`) | Symbol: `test_config_schema_theme_is_dynamic_string_not_enum` | Role: *Theme configuration schema validation and dynamic source handling* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect theme registry and initialization flow**: Inspect scan_installed_packages in crates/fresh-editor/src/app/editor_init.rs to understand how built-in themes and theme packages are loaded and registered at startup. (Target: `crates/fresh-editor/src/app/editor_init.rs`)
2. **Verify theme configuration schema and validation**: Examine test_config_schema_theme_is_dynamic_string_not_enum in crates/fresh-editor/src/config.rs to verify that theme names accept dynamic strings and ensure proper fallback behavior. (Target: `crates/fresh-editor/src/config.rs`)
3. **Add Tokyo Night theme definition or asset**: Incorporate the missing Tokyo Night theme definition into the built-in themes collection or ensure it is correctly bundled and loaded by the theme registry. (Target: `crates/fresh-editor/src/app/editor_init.rs`)
4. **Add regression test and execute cargo test**: Add a unit test in crates/fresh-editor/src/config.rs verifying that the Tokyo Night theme is successfully present in the available theme selection list upon initialization, then run cargo test. (Target: `crates/fresh-editor/src/config.rs`)

## 5. Educational Concepts
### Theme Registry and Loading
- **What is it:** The mechanism by which the editor discovers, loads, and registers themes from disk or built-in assets.
- **Why it matters:** Understanding how themes are loaded allows developers to ensure new or built-in themes are correctly recognized by the application.
- **Connection to Issue:** Directly explains why a theme listed in documentation might be missing from the runtime selection list if it is not registered or bundled properly.

### Dynamic Configuration Schema
- **What is it:** A configuration design where allowed values are loaded dynamically rather than being hardcoded into a static enum.
- **Why it matters:** Prevents rigid schema validation errors when user-defined or newly added themes are used.
- **Connection to Issue:** Relates to how theme options are exposed and validated across the application configuration and schema.

