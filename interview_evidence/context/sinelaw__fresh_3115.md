# Issue Context Dossier: `sinelaw/fresh` #3115

**Title:** textmate_grammar option is undocumented and only supports .sublime-syntax despite its name  
**Repository:** https://github.com/sinelaw/fresh  
**Language:** Rust  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The `textmate_grammar` configuration option in the editor's language settings is undocumented and its name is misleading, as it currently only supports `.sublime-syntax` files rather than true TextMate `.tmLanguage` files, throwing an unsupported format error when `.tmLanguage` is provided.

## 2. Root Cause Analysis
> The option was named `textmate_grammar` historically or loosely, but the underlying grammar parser or loader implementation explicitly expects and processes Sublime text syntax format (`.sublime-syntax`), resulting in a format validation check failure when a TextMate XML/plist (`.tmLanguage`) file is passed.

## 3. Grounded Code Locations & Citations
- File: `crates/fresh-editor/src/config.rs` (Lines: `4551-4590`) | Symbol: `LanguageConfig` | Role: *Defines language configuration fields including textmate_grammar* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect LanguageConfig in crates/fresh-editor/src/config.rs**: Inspect the LanguageConfig struct in crates/fresh-editor/src/config.rs to understand how textmate_grammar is documented and defined. (Target: `crates/fresh-editor/src/config.rs`)
2. **Update Documentation Comments for textmate_grammar**: Add explicit documentation comments to the textmate_grammar field in LanguageConfig explaining that the option accepts only .sublime-syntax files despite its historical name. (Target: `crates/fresh-editor/src/config.rs`)
3. **Add Unit Tests for Configuration Documentation and Parsing**: Add or update configuration tests in crates/fresh-editor/src/config.rs to verify that LanguageConfig correctly deserializes and documents textmate_grammar. (Target: `crates/fresh-editor/src/config.rs`)
4. **Run Test Suite Using Verified Command**: Run cargo test to ensure all tests pass successfully without any regressions introduced by the updated configuration documentation. (Target: `None`)

## 5. Educational Concepts
### Configuration Schema and Documentation Alignment
- **What is it:** Ensuring configuration keys and option names accurately reflect their underlying capabilities and are properly documented for users.
- **Why it matters:** When configuration options have misleading names or lack documentation, users experience confusion and runtime errors trying to guess supported file formats.
- **Connection to Issue:** Directly addresses the user experience gap where `textmate_grammar` implies TextMate format support (`.tmLanguage`) but actually requires `.sublime-syntax`, which needs to be clarified in documentation.

### Editor Syntax Grammar Loading
- **What is it:** The mechanism by which text editors load syntax highlighting rules from external files for custom languages.
- **Why it matters:** Editors rely on specific grammar specifications to tokenize text and provide syntax highlighting features.
- **Connection to Issue:** Explains why the editor validates file extensions or grammar formats during startup or configuration loading.

