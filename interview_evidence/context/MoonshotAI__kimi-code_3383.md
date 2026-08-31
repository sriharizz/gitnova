# Issue Context Dossier: `MoonshotAI/kimi-code` #3383

**Title:** Read.line_offset: anyOf integer 参数在第三方模型下 100% 失败（同版本数字形态正常，附Windows + Qwen3.8-Flash 复现）  
**Repository:** https://github.com/MoonshotAI/kimi-code  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The Read tool's line_offset parameter fails when using third-party OpenAI-compatible models (like Qwen3.8-Flash) because these models serialize scalar integer arguments as JSON strings (e.g., "line_offset": "200"). The validation layer uses Ajv with type coercion disabled and a complex anyOf schema, resulting in an 'Invalid args' error and preventing tool execution.

## 2. Root Cause Analysis
> Third-party LLM providers serialize integer parameters into string representations in their tool call arguments (e.g., "line_offset": "200"). When validated against the tool schema using Ajv without type coercion enabled, strict type checking rejects the string values because they do not strictly match the expected integer/number type in the anyOf union.

## 3. Grounded Code Locations & Citations
- File: `apps/kimi-code/src/main.ts` (Lines: `1-40`) | Symbol: `None` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Ajv Validation Configuration**: Inspect the Ajv validation setup in apps/kimi-code/src/main.ts to locate where tool argument validation and schema definitions (specifically for line_offset and anyOf unions) are initialized. (Target: `apps/kimi-code/src/main.ts`)
2. **Enable Type Coercion in Ajv Instance**: Update the Ajv validator instantiation in apps/kimi-code/src/main.ts to enable type coercion (setting { coerceTypes: true } or configuring appropriate options) so that string-serialized integer parameters like line_offset (e.g. "200") are properly coerced to numbers before schema validation. (Target: `apps/kimi-code/src/main.ts`)
3. **Add Regression Test for String-Serialized Numeric Arguments**: Add a unit/integration test case verifying that the Read tool successfully processes tool call arguments where numeric parameters like line_offset are passed as strings (e.g., {"line_offset": "200"}) without throwing an 'Invalid args' error. (Target: `apps/kimi-code/src/main.ts`)
4. **Run Test Suite**: Execute the verified test command to verify that all tests pass successfully and the regression is fully resolved. (Target: `None`)

## 5. Educational Concepts
### JSON Schema Type Coercion in Ajv
- **What is it:** Type coercion allows a validation library to automatically convert input types (like a string containing a number "200") into the expected target type (like the integer 200) before validation.
- **Why it matters:** Different LLM providers serialize JSON tool call arguments differently; enabling type coercion ensures that minor serialization differences do not break tool execution.
- **Connection to Issue:** Enabling coercion or handling string-wrapped numbers in the validator prevents third-party model outputs from failing strict schema validation.

### Handling Union Schemas (anyOf)
- **What is it:** An anyOf schema validation rule requires that the provided data matches at least one of the specified sub-schemas.
- **Why it matters:** Complex union schemas can make validation stricter and harder for external models to satisfy if type matching is rigid.
- **Connection to Issue:** The line_offset parameter uses a compound anyOf integer schema which exacerbates strict type rejection when values arrive as strings.

