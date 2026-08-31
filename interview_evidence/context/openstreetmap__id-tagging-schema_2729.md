# Issue Context Dossier: `openstreetmap/id-tagging-schema` #2729

**Title:** add shop=eggs as egg vending machine is in presets?  
**Repository:** https://github.com/openstreetmap/id-tagging-schema  
**Language:** JSON  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The issue requests adding 'shop=eggs' as a preset to prevent mistagging of egg shops as egg vending machines, as egg vending machines are already supported in presets.

## 2. Root Cause Analysis
> The preset definition file lacks an entry for 'shop=eggs' because it has not yet been added to the repository's configuration data.

## 3. Grounded Code Locations & Citations
- File: `eslint.config.js` (Lines: `1-145`) | Symbol: `None` | Role: *Linter configuration file* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect existing preset definitions**: Inspect existing shop preset definitions in the codebase to understand the required structure for adding shop=eggs. (Target: `data/presets.json`)
2. **Add shop=eggs preset entry**: Define the new preset entry for shop=eggs with appropriate tags, icon, and name metadata in the preset data file. (Target: `data/presets.json`)
3. **Run tests and linter**: Run npm test and npm run lint to verify the schema updates and ensure no lint errors or test failures are introduced. (Target: `vitest.config.js`)

## 5. Educational Concepts
### OSM Preset Definition
- **What is it:** A configuration structure that maps specific OpenStreetMap tags to user-friendly UI presets in map editors like iD.
- **Why it matters:** Presets make it easy for everyday mappers to correctly categorize features without needing to memorize raw key-value pairs.
- **Connection to Issue:** Adding 'shop=eggs' requires defining a new preset entry so editors recognize the tag and offer it in the user interface.

### Data-Driven Tagging Schemas
- **What is it:** A pattern where map features and UI metadata are maintained in structured JSON data files rather than hardcoded in application logic.
- **Why it matters:** It allows community contributors to easily update tagging standards and presets by modifying JSON files.
- **Connection to Issue:** Contributors implement new tags and presets by updating the schema data files located in the repository.

