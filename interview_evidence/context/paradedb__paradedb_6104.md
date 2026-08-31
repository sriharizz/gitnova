# Issue Context Dossier: `paradedb/paradedb` #6104

**Title:** Range-partitioned JoinScan converts sampled NUMERIC partition bounds twice  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Range-partitioned JoinScan samples `partition_by` fast fields in their raw/stored form, but then wraps these split points in normal `pdb::Query::Range` filters. Because `pdb::Query::Range` automatically runs `scale_numeric_bound` on `Numeric64` fields and parses `NumericBytes` bounds, sampled numeric partition bounds get converted twice or trigger conversion errors.

## 2. Root Cause Analysis
> The root cause is a mismatch between how user-provided query bounds and sampled partition bounds are processed. `pdb::Query::Range` assumes input bounds are logical user inputs that require scaling (`scale_numeric_bound`) or byte-conversion (`numeric_bound_to_bytes`). However, range-partitioned join scans supply already-stored internal fast field values, leading to duplicate scaling for `Numeric64` and invalid type conversion errors for `NumericBytes`.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1541-1580`) | Symbol: `range` | Role: *Applies numeric scaling and byte conversion to range bounds* (Verified: True)
- File: `pg_search/src/index/fast_fields_helper.rs` (Lines: `351-390`) | Symbol: `WhichFastField` | Role: *Defines fast field requests used to fetch stored column values* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect pdb::Query::Range handling**: Inspect the range query construction and execution logic in pg_search/src/query/pdb_query.rs to understand how scale_numeric_bound and numeric_bound_to_bytes are applied. (Target: `pg_search/src/query/pdb_query.rs`)
2. **Inspect sample_fast_field and WhichFastField usage**: Examine how WhichFastField and sample_fast_field extract raw/stored partition bounds in pg_search/src/index/fast_fields_helper.rs. (Target: `pg_search/src/index/fast_fields_helper.rs`)
3. **Prevent double scaling or conversion for sampled bounds**: Modify the range query constructor or introduce a dedicated variant/flag in pg_search/src/query/pdb_query.rs so that sampled numeric or byte partition bounds bypass redundant scaling and byte conversion. (Target: `pg_search/src/query/pdb_query.rs`)
4. **Add regression test and verify with cargo test**: Add a regression test case covering range-partitioned join scans on Numeric64 and NumericBytes columns, then execute the verified test command to ensure correctness. (Target: `pg_search/src/query/pdb_query.rs`)

## 5. Educational Concepts
### Fixed-Point Numeric Scaling
- **What is it:** A technique where decimals are stored as scaled integers (e.g., multiplying by 10^scale) to avoid floating-point inaccuracies.
- **Why it matters:** Developers must ensure scaling is applied exactly once during round-tripping to prevent data corruption or skewed partitions.
- **Connection to Issue:** Sampled `Numeric64` bounds are already stored in their scaled form, but passing them through `range()` applies scaling a second time.

### Query Range Bounding
- **What is it:** The mechanism that translates high-level search range bounds (inclusive/exclusive/unbounded) into low-level query terms.
- **Why it matters:** Query filters must accurately interpret boundaries to return correct search results without runtime type errors.
- **Connection to Issue:** `NumericBytes` range bounds expect sortable byte representations, but raw sampled bytes fail validation when treated as unencoded inputs.

