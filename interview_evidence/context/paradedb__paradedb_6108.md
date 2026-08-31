# Issue Context Dossier: `paradedb/paradedb` #6108

**Title:** Sequential scan fallback returns no rows for NUMERIC key fields  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When executing a sequential-scan fallback query on a PostgreSQL `NUMERIC` key field in ParadeDB, zero rows are returned because the fallback reads index keys using physical storage representations (like `Numeric64` or `NumericBytes`) while heap keys are parsed naively as raw dataums without applying the index schema conversion.

## 2. Root Cause Analysis
> During sequential scan fallback evaluation, the keyset collection logic mismatch between index storage formats (`Numeric64` and `NumericBytes`) and raw heap datums (`NUMERICOID` standard conversion) results in incompatible internal representations (e.g., comparing an `I64` or `Bytes` representation against a string or untransformed datum), causing exact value lookups in `KeySet` to fail.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/postgres/utils.rs` (Lines: `876-915`) | Symbol: `scalar_datum_to_tantivy_value` | Role: *Relevant Code* (Verified: True)
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1541-1580`) | Symbol: `range` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect scalar_datum_to_tantivy_value in pg_search/src/postgres/utils.rs**: Examine how scalar_datum_to_tantivy_value handles NUMERICOID datums and whether it has access to index schema formatting options such as Numeric64 or NumericBytes. (Target: `pg_search/src/postgres/utils.rs`)
2. **Analyze sequential-scan fallback keyset collection in pg_search/src/query/pdb_query.rs**: Inspect how collect_keyset retrieves index keys and how heap keys are evaluated during sequential-scan fallback, identifying the mismatch between physical index representations and raw heap datums. (Target: `pg_search/src/query/pdb_query.rs`)
3. **Apply schema-aware conversion for NUMERIC keys**: Update the heap key conversion logic or fallback evaluation in pg_search/src/query/pdb_query.rs to utilize the correct index schema-aware conversion matching the index format version (e.g. Numeric64 or NumericBytes). (Target: `pg_search/src/query/pdb_query.rs`)
4. **Add regression test and run test command**: Add an integration or unit test verifying that queries filtering on PostgreSQL NUMERIC key fields with sequential-scan fallback successfully return matching rows, and run cargo test to verify. (Target: `pg_search/src/query/pdb_query.rs`)

## 5. Educational Concepts
### Schema-Aware Datum Conversion
- **What is it:** Converting raw PostgreSQL database values (datums) into indexed search types using the specific schema rules defined for that index field.
- **Why it matters:** Different index configurations store numeric data differently (e.g., fixed-precision integers or byte arrays), so reading or comparing values requires matching the exact schema encoding rules rather than using default type conversions.
- **Connection to Issue:** The fallback mechanism currently fails because it compares heap values converted with default rules against index values stored with schema-specific numeric representations.

### Sequential Scan Fallback
- **What is it:** A fallback execution path where PostgreSQL evaluates search operators (like `@@@`) via sequential table scans when index scans are disabled or unavailable.
- **Why it matters:** Ensures correctness and query execution even when specialized index access methods are bypassed by query planners or user settings.
- **Connection to Issue:** The bug specifically manifests under sequential scan fallbacks when filtering rows containing `NUMERIC` key fields.

