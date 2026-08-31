# Issue Context Dossier: `paradedb/paradedb` #6101

**Title:** BM25 indexes reject valid NUMERIC typmods with |scale| > 18  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> PostgreSQL NUMERIC(precision, scale) columns with |scale| > 18 fail when building a BM25 index or initializing an empty index due to the representation-selection logic incorrectly choosing Numeric64 even when the scale exceeds the bounds supported by Decimal64NoScale (-18 through 18).

## 2. Root Cause Analysis
> `SearchFieldType::try_from_type_info` or equivalent configuration builders inspect precision to choose `Numeric64` but fail to validate that the absolute scale is within the 18-scale limit mandated by `Decimal64NoScale`.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/postgres/utils.rs` (Lines: `946-985`) | Symbol: `extract_numeric_precision_scale` | Role: *Extracts precision and scale from PostgreSQL NUMERIC typmod* (Verified: True)
- File: `pg_search/src/schema/config.rs` (Lines: `281-320`) | Symbol: `default_numeric_bytes` | Role: *Provides alternative numeric bytes representation for wide precision or scales* (Verified: True)
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1541-1580`) | Symbol: `range` | Role: *Handles numeric bound scaling based on selected field type* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect extract_numeric_precision_scale and representation selection**: Inspect extract_numeric_precision_scale in pg_search/src/postgres/utils.rs and the field configuration builders in pg_search/src/schema/config.rs to understand how precision and scale are currently evaluated for choosing Numeric64 versus NumericBytes. (Target: `pg_search/src/postgres/utils.rs`)
2. **Update numeric representation selection logic for scale bounds**: Modify the schema configuration logic to verify that not only is precision <= 18, but the absolute scale (|scale| <= 18) is also within the supported range of Decimal64NoScale before selecting Numeric64; otherwise, fall back to NumericBytes. (Target: `pg_search/src/schema/config.rs`)
3. **Add a regression test for NUMERIC with scale > 18**: Add a new test case to the test suite that defines a table with a NUMERIC(precision, scale) column where precision <= 18 but scale > 18 (e.g., NUMERIC(10, 20)), initializes a BM25 index on it, and verifies that index creation and queries succeed without failing on Decimal64NoScale range limits. (Target: `pg_search/tests/integration_tests.rs`)
4. **Run test suite verification**: Run cargo test to verify that all existing tests pass and the new regression test correctly validates the wide scale NUMERIC field mapping. (Target: `None`)

## 5. Educational Concepts
### PostgreSQL NUMERIC Typmod Encoding
- **What is it:** PostgreSQL encodes column precision and scale metadata into an integer called a typmod.
- **Why it matters:** Extensions must correctly decode typmods to understand the decimal constraints and numeric ranges defined by users.
- **Connection to Issue:** The issue stems from correctly extracting the scale but failing to validate it against the limits of the chosen backend encoder.

### Fixed-Point Numeric Representations (Numeric64 vs NumericBytes)
- **What is it:** Choice between fast 64-bit integer storage (Numeric64) and flexible byte-encoded storage (NumericBytes) for decimals.
- **Why it matters:** Numeric64 offers high performance but has strict precision and scale boundaries (-18 to 18), whereas NumericBytes supports arbitrary precision and scale.
- **Connection to Issue:** The selection logic must evaluate whether the column's scale exceeds 18 so it can fall back to NumericBytes instead of crashing in Decimal64NoScale.

