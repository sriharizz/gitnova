# Issue Context Dossier: `openstreetmap/id-tagging-schema` #2047

**Title:** Add priority=* field to traffic_calming=choker  
**Repository:** https://github.com/openstreetmap/id-tagging-schema  
**Language:** JSON  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Issue #2047 proposes updating the OpenStreetMap tagging presets in `openstreetmap/id-tagging-schema` to replace the `direction=*` field with a `priority=*` field for the `traffic_calming=choker` preset.

## 2. Root Cause Analysis
> Preset definitions in the tagging schema repository are defined in data configuration files. The `traffic_calming=choker` preset currently references the direction field rather than the priority field.

## 3. Grounded Code Locations & Citations
- File: `eslint.config.js` (Lines: `1-40`) | Symbol: `block_1` | Role: *Linter and configuration context* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect traffic_calming=choker preset definition**: Locate and inspect the preset definition for traffic_calming=choker in the tagging schema preset data files to verify its current fields including direction=*. (Target: `data/presets/traffic_calming/choker.json`)
2. **Remove direction=* field and add priority=* field**: Modify the preset definition to remove the redundant direction=* field and add the priority=* field for traffic_calming=choker. (Target: `data/presets/traffic_calming/choker.json`)
3. **Run schema validation tests**: Execute the test suite to verify that the preset schema validation passes successfully with the updated fields. (Target: `package.json`)

## 5. Educational Concepts
### Tagging Schema Presets
- **What is it:** JSON-based configuration files that define how map features and their attributes appear in OpenStreetMap editors.
- **Why it matters:** Understanding preset schemas allows developers to correctly add, remove, or modify fields and tags presented to users during map editing.
- **Connection to Issue:** Fixing this issue involves updating the preset definition for `traffic_calming=choker` to swap the `direction` field for the `priority` field.

### Codebase Linter Rules
- **What is it:** Automated checks enforced by tools like ESLint to ensure code and data formatting rules are met.
- **Why it matters:** Running linters locally prevents CI build failures due to formatting or duplicate key errors.
- **Connection to Issue:** Contributors must ensure any modified preset files adhere to local JSON and sorting rules enforced in eslint.config.js.

