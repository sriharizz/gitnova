# Issue Context Dossier: `openstreetmap/id-tagging-schema` #2780

**Title:** support emergency=access_point as unsearchable duplicate of highway=emergency_access_point ?  
**Repository:** https://github.com/openstreetmap/id-tagging-schema  
**Language:** JSON  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> This issue proposes supporting `emergency=access_point` as an unsearchable duplicate of `highway=emergency_access_point` in the OpenStreetMap iD tagging schema.

## 2. Root Cause Analysis
> The tag `emergency=access_point` was introduced via mass imports and community usage, but the iD tagging schema definitions do not yet map it as a duplicate or discarded variant of `highway=emergency_access_point`.

## 3. Grounded Code Locations & Citations
- File: `eslint.config.js` (Lines: `1-40`) | Symbol: `None` | Role: *Configuration file referencing dataset paths like discarded.json and deprecated.json* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect discarded tags configuration**: Inspect data/discarded.json to understand how unsearchable duplicate tags are structured and integrated into the iD tagging schema. (Target: `data/discarded.json`)
2. **Add emergency=access_point as a discarded duplicate**: Add an entry for emergency=access_point in data/discarded.json mapping it to highway=emergency_access_point as an unsearchable duplicate tag. (Target: `data/discarded.json`)
3. **Run test suite and linter**: Execute the repository test command and linter to verify that the newly added schema entry conforms to validation rules and does not introduce syntax or schema errors. (Target: `None`)

## 5. Educational Concepts
### Tag Discarding and Duplicates in OpenStreetMap iD
- **What is it:** A mechanism to handle deprecated, alternate, or mass-imported tags by marking them as unsearchable duplicates of canonical tags.
- **Why it matters:** Keeps map data clean and ensures search queries and editors point users toward the canonical tag (`highway=emergency_access_point`) rather than alternate variations.
- **Connection to Issue:** The issue requests adding `emergency=access_point` as an unsearchable duplicate so that editors and schema validations treat it accordingly.

### JSON Data Configuration Files
- **What is it:** Structured JSON files used in the repository to store metadata about map features, tags, presets, and discarded items.
- **Why it matters:** Allows configuration-driven definition of map tags without needing deep code changes.
- **Connection to Issue:** Adding or mapping the tag involves updating schema JSON definitions.

