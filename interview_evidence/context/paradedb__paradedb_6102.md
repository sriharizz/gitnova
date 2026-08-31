# Issue Context Dossier: `paradedb/paradedb` #6102

**Title:** Numeric64 pushdown rounds query literals and changes comparison semantics  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Predicate pushdown on `Numeric64` fields rounds query literals to the column's declared scale before building the Tantivy query. This causes off-grid or high-precision literals (e.g., `12.345` on a scale-2 column) to be incorrectly rounded (becoming `12.35`), altering comparison semantics and returning incorrect query results compared to native PostgreSQL.

## 2. Root Cause Analysis
> The query evaluation path in `pg_search/src/query/pdb_query.rs` invokes `scale_numeric_bound()` for `SearchFieldType::Numeric64(_, scale)`, which applies the column's scaling and rounding logic designed for encoding stored table data to query operands, improperly quantizing filter literals.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1541-1580`) | Symbol: `range` | Role: *Handles `SearchFieldType::Numeric64` range query translation and applies scaling bounds.* (Verified: True)
- File: `pg_search/src/api/builder_fns/paradedb.rs` (Lines: `106-145`) | Symbol: `term_with_operator` | Role: *Constructs fielded queries and range queries from SQL operator predicates.* (Verified: True)
- File: `pg_search/src/postgres/utils.rs` (Lines: `946-985`) | Symbol: `extract_numeric_precision_scale` | Role: *Extracts precision and scale from PostgreSQL NUMERIC typmod.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect query scaling logic in pdb_query.rs**: Examine how scale_numeric_bound is called for SearchFieldType::Numeric64 within pg_search/src/query/pdb_query.rs to understand how query literals are rounded. (Target: `pg_search/src/query/pdb_query.rs`)
2. **Review term and range query builders in paradedb.rs**: Check pg_search/src/api/builder_fns/paradedb.rs to verify how operator predicates construct range and term queries and interact with numeric scales. (Target: `pg_search/src/api/builder_fns/paradedb.rs`)
3. **Adjust numeric boundary handling for query literals**: Modify the predicate pushdown logic in pg_search/src/query/pdb_query.rs to prevent inappropriate rounding/quantization of query literals that exceed the column scale, aligning behavior with PostgreSQL comparison semantics. (Target: `pg_search/src/query/pdb_query.rs`)
4. **Add regression test and run test suite**: Add a regression test verifying that high-precision query literals on Numeric64 columns (e.g., 12.345 on a scale-2 column) evaluate correctly without incorrect rounding, then run cargo test. (Target: `pg_search/src/query/pdb_query.rs`)

## 5. Educational Concepts
### Fixed-Point Numeric Scaling vs. Query Bounds
- **What is it:** The distinction between formatting stored column values to fit a fixed scale and interpreting precise query literals during predicate evaluation.
- **Why it matters:** Applying storage encoding rules directly to query parameters alters query semantics, turning strict inequality or off-grid range checks into rounded value comparisons.
- **Connection to Issue:** Fixing this requires separating how stored column values are converted from how query bounds and comparison literals are evaluated against index bounds.

### Predicate Pushdown Bound Translation
- **What is it:** Translating SQL comparisons (`=`, `<`, `<=`, etc.) into index-level query bounds that respect database comparison semantics.
- **Why it matters:** Index-accelerated scans must produce identical result sets to sequential scans; otherwise, indexes yield incorrect data filtering.
- **Connection to Issue:** The bug arises because `scale_numeric_bound` rounds off fractional digits prematurely when mapping SQL query literals into `Numeric64` filter bounds.

