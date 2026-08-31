# Issue Context Dossier: `openstreetmap/id-tagging-schema` #2759

**Title:** support =designated in manyCombo  
**Repository:** https://github.com/openstreetmap/id-tagging-schema  
**Language:** JSON  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Issue #2759 in openstreetmap/id-tagging-schema proposes supporting `=designated` values within `manyCombo` field types. This involves updating tag definitions or field configurations in the tagging schema data files.

## 2. Root Cause Analysis
> The schema definitions or field configurations lack explicit inclusion or default application for `=designated` in combinations, which restricts field choices in downstream OpenStreetMap editing tools.

## 3. Grounded Code Locations & Citations
- File: `eslint.config.js` (Lines: `1-40`) | Symbol: `block_1` | Role: *Configuration file showing project setup* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect manyCombo field configurations**: Inspect existing manyCombo field definitions and schema specifications in the repository data files to locate where designated values need to be supported. (Target: `data/fields.json`)
2. **Add designated option to target manyCombo fields**: Update the relevant field configurations in data files to explicitly include `=designated` values for the identified manyCombo fields. (Target: `data/fields.json`)
3. **Add regression test for manyCombo designated values**: Create or update test cases to verify that manyCombo fields correctly accept and validate designated values without error. (Target: `vitest.config.js`)
4. **Run test suite**: Execute the test command to verify that all schema tests pass successfully with the new manyCombo configurations. (Target: `None`)

## 5. Educational Concepts
### Tagging Schema Definition
- **What is it:** JSON-based structured configurations defining how OpenStreetMap tags and fields behave in editing interfaces.
- **Why it matters:** Developers need to understand schema files to correctly add, modify, or extend UI field types and tag options.
- **Connection to Issue:** Fixing this issue requires updating schema properties or field configurations where `manyCombo` is defined.

### Schema Versioning
- **What is it:** Incrementing version numbers associated with schema definitions when breaking or significant additions are made.
- **Why it matters:** Ensures downstream consumers and parsers recognize updates to tag specifications.
- **Connection to Issue:** The issue author asks whether bumping the schema version is necessary for supporting `=designated`.

