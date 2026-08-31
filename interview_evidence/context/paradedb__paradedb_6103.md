# Issue Context Dossier: `paradedb/paradedb` #6103

**Title:** more_like_this fails or silently returns no rows for NUMERIC fields  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The key-value form of `pdb.more_like_this` mishandles PostgreSQL `NUMERIC` fields. Specifically, `Numeric64` fields raise an internal query-construction error due to uncoerced string storage, and `NumericBytes` fields are silently ignored and return no rows because Tantivy MoreLikeThis ignores `Bytes` fields or lacks proper support.

## 2. Root Cause Analysis
> The query builder parses values from the seed row without accounting for schema-specific numeric storage representations (`Numeric64` and `NumericBytes`), passing raw string representations or un-scaled values into Tantivy's MoreLikeThis query engine which expects specific primitive types or correctly formatted byte encodings.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/api/builder_fns/pdb.rs` (Lines: `211-250`) | Symbol: `range_numeric` | Role: *Relevant Code* (Verified: True)
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1541-1580`) | Symbol: `range` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect pdb.more_like_this and numeric handling in pdb.rs**: Examine pg_search/src/api/builder_fns/pdb.rs to inspect how seed row values are retrieved and converted into PdbOwnedValue, specifically checking how Numeric64 and NumericBytes types are handled. (Target: `pg_search/src/api/builder_fns/pdb.rs`)
2. **Inspect query construction logic in pdb_query.rs**: Inspect pg_search/src/query/pdb_query.rs to understand how MoreLikeThis queries pass field values to Tantivy and how numeric type casting or conversion fails for Numeric64 and NumericBytes. (Target: `pg_search/src/query/pdb_query.rs`)
3. **Implement correct schema-aware type coercion for Numeric64 and NumericBytes**: Update the value conversion and query generation logic in pdb.rs and pdb_query.rs so that Numeric64 values are correctly mapped to integer types expected by Tantivy's MoreLikeThis query engine, and NumericBytes are either properly encoded or return a clear error. (Target: `pg_search/src/api/builder_fns/pdb.rs`)
4. **Add regression test and run test suite**: Add a new SQL/Rust regression test verifying that pdb.more_like_this successfully queries Numeric64 fields without raising an invalid value error, then run cargo test to verify the fix. (Target: `pg_search/src/api/builder_fns/pdb.rs`)

## 5. Educational Concepts
### Schema-Aware Value Conversion
- **What is it:** Translating database values into the exact internal format expected by search indexes based on field definitions.
- **Why it matters:** Search indexes store numerical data in optimized formats (like fixed-point integers or byte arrays). Failing to convert database datums correctly leads to runtime type mismatch errors or silent query failures.
- **Connection to Issue:** The key-value path of `pdb.more_like_this` fails because it passes string-encoded values to fields expecting `Numeric64` or `NumericBytes` storage formats.

### PostgreSQL Numeric Datatypes in Search
- **What is it:** Handling PostgreSQL's arbitrary-precision numeric types within Tantivy search and retrieval queries.
- **Why it matters:** PostgreSQL numeric values have high precision and require special scaling or byte serialization to be indexed and queried efficiently in Rust search backends.
- **Connection to Issue:** `NUMERIC` fields can map to either `Numeric64` or `NumericBytes` representations in ParadeDB, each requiring distinct handling during query construction.

