# Issue Context Dossier: `sinelaw/fresh` #3114

**Title:** Docs: Missing documentation and examples for use_tabs / use_spaces configuration  
**Repository:** https://github.com/sinelaw/fresh  
**Language:** Rust  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The documentation for the `fresh` text editor lacks clear instructions and code examples for configuring indentation via `use_tabs` and `use_spaces`, making it difficult for users to customize how tabs and spaces are handled globally or per-language.

## 2. Root Cause Analysis
> The issue stems from missing documentation coverage for the `use_tabs` configuration option and related indentation settings defined in the editor's configuration modules.

## 3. Grounded Code Locations & Citations
- File: `crates/fresh-editor/src/config.rs` (Lines: `3150-3155`) | Symbol: `indent_string` | Role: *Defines effective indentation string behavior based on use_tabs and tab_size* (Verified: True)
- File: `crates/fresh-editor/src/partial_config.rs` (Lines: `876-915`) | Symbol: `partial_config` | Role: *Handles partial configuration parsing for editor settings* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect configuration control flow and indentation fields**: Inspect symbol `indent_string` in `crates/fresh-editor/src/config.rs` and partial configuration parsing in `crates/fresh-editor/src/partial_config.rs` to understand how `use_tabs` and `tab_size` are structured. (Target: `crates/fresh-editor/src/config.rs`)
2. **Draft documentation and configuration examples**: Add clear instructions, markdown documentation, or configuration code snippets explaining how to configure `use_tabs` and `tab_size` both globally and per-language overrides. (Target: `crates/fresh-editor/src/config.rs`)
3. **Run cargo test to verify existing configuration tests**: Run the test suite using `cargo test` to ensure that configuration parsing and editor tests continue to pass without regressions after any doc comment or documentation updates. (Target: `None`)

## 5. Educational Concepts
### Editor Configuration & Indentation
- **What is it:** Settings that control whether the editor uses hard tab characters or spaces for indentation.
- **Why it matters:** Users need predictable indentation behavior matching their project's coding style guidelines.
- **Connection to Issue:** Directly relates to documenting the `use_tabs` and space indentation settings.

### Documentation and Examples
- **What is it:** Clear Markdown guides and configuration code snippets that demonstrate feature usage to end users.
- **Why it matters:** Without examples, users cannot easily discover or correctly format configuration options.
- **Connection to Issue:** Addressing the issue requires adding missing documentation sections and YAML/TOML snippets for indentation configuration.

