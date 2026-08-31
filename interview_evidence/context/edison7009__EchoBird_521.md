# Issue Context Dossier: `edison7009/EchoBird` #521

**Title:** Codex 集成下视觉模型被误判为纯文本模型，无法上传图片  
**Repository:** https://github.com/edison7009/EchoBird  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When integrating vision models (such as deepseek-v4-flash-vision-exp) through EchoBird's Codex integration, EchoBird generates the ~/.codex/models.json configuration file with input_modalities hardcoded to ["text"]. Consequently, Codex treats the model as a text-only model and blocks image uploads with the error "This model does not support image inputs".

## 2. Root Cause Analysis
> EchoBird uses compiled-in capability templates and model catalog generation routines (such as those in src-tauri/src/services/codex_catalog.rs) which declare fixed input modalities like ["text"] or lack a dynamic check for vision capability on third-party responses passthrough endpoints.

## 3. Grounded Code Locations & Citations
- File: `src-tauri/src/services/codex_catalog.rs` (Lines: `1-40`) | Symbol: `DEEPSEEK_TEMPLATE` | Role: *Defines DeepSeek capability template embedded via include_str! where input modalities are declared.* (Verified: True)
- File: `src-tauri/src/services/codex_catalog.rs` (Lines: `36-75`) | Symbol: `template_for_url` | Role: *Matches provider base_url to bundled capability templates.* (Verified: True)
- File: `src-tauri/src/services/codex_proxy/content_mapper.rs` (Lines: `1-40`) | Symbol: `map_content_part` | Role: *Maps Responses API content parts (like input_image) to Chat Completions format.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect DEEPSEEK_TEMPLATE and model catalog logic**: Inspect DEEPSEEK_TEMPLATE and template_for_url in src-tauri/src/services/codex_catalog.rs to verify how input modalities are currently hardcoded or mapped. (Target: `src-tauri/src/services/codex_catalog.rs`)
2. **Update capability template input modalities**: Modify DEEPSEEK_TEMPLATE and associated vendor templates within src-tauri/src/services/codex_catalog.rs to support ["text", "image"] input modalities for multimodal models. (Target: `src-tauri/src/services/codex_catalog.rs`)
3. **Inspect map_content_part for content mapping**: Review map_content_part in src-tauri/src/services/codex_proxy/content_mapper.rs to ensure image content parts are correctly routed when multimodal modalities are enabled. (Target: `src-tauri/src/services/codex_proxy/content_mapper.rs`)
4. **Add regression test for model catalog generation**: Add a unit test in src-tauri/src/services/tool_config_manager.rs or codex_catalog.rs verifying that vision-capable models correctly serialize input_modalities including both text and image. (Target: `src-tauri/src/services/tool_config_manager.rs`)
5. **Run test suite**: Run Cargo test to verify that all catalog generation and content mapping tests pass successfully. (Target: `None`)

## 5. Educational Concepts
### Model Input Modalities Declaration
- **What is it:** A configuration field (input_modalities) that informs client applications like Codex whether a model accepts only text or also images and other media.
- **Why it matters:** Client applications inspect these metadata declarations to enable or disable UI buttons such as image uploaders before sending requests.
- **Connection to Issue:** EchoBird hardcodes input_modalities to ["text"] in its generated catalog/template, causing Codex to falsely assume the model is text-only.

### Compiled Capability Templates
- **What is it:** Static JSON templates embedded into the Rust binary at compile time using macros like include_str! to configure third-party tool integrations.
- **Why it matters:** They provide reproducible, fast configurations for external AI coding assistants without needing dynamic file lookups at runtime.
- **Connection to Issue:** The DeepSeek template embedded in the codebase dictates the static input modalities written into ~/.codex/models.json on every startup.

