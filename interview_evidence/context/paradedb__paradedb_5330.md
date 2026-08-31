# Issue Context Dossier: `paradedb/paradedb` #5330

**Title:** High-cardinality GROUP BY shuffle dominated by per-frame Arrow IPC encode  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> High-cardinality GROUP BY queries running under ParadeDB's MPP framework suffer from poor performance due to excessive per-frame Arrow IPC serialization overhead during hash shuffle and a non-reducing partial pre-aggregation stage that unnecessarily passes full row counts through a hash pass.

## 2. Root Cause Analysis
> The root cause stems from the MPP shuffle transport layer encoding self-contained Arrow IPC streams per frame with repeated schema definitions, combined with an eager partial aggregation stage that performs a hash pass even when row reduction is negligible.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/gucs.rs` (Lines: `141-180`) | Symbol: `MPP_QUEUE_SIZE` | Role: *Defines MPP shuffle queue and ring size GUC parameters governing shuffle backpressure and frame sizing.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect MPP GUC configurations**: Inspect symbol MPP_QUEUE_SIZE and related shuffle settings in pg_search/src/gucs.rs to understand queue sizing and frame serialization parameters. (Target: `pg_search/src/gucs.rs`)
2. **Optimize Arrow IPC serialization overhead**: Modify the MPP hash shuffle transport layer to write the Arrow schema once per channel rather than redundantly per frame, reducing overhead during high-cardinality GROUP BY execution. (Target: `pg_search/src/gucs.rs`)
3. **Implement batch coalescing and pre-aggregation bypass**: Add logic to coalesce small per-partition batches before encoding and conditionally bypass the partial pre-aggregation stage when estimated cardinality approaches the input row count. (Target: `pg_search/src/gucs.rs`)
4. **Add regression test for high-cardinality GROUP BY**: Implement a regression test covering high-cardinality GROUP BY queries under the MPP framework to assert correct performance and output correctness. (Target: `pg_search/src/gucs.rs`)
5. **Run test suite verification**: Run cargo test to ensure all existing and newly added regression tests pass successfully without regressions. (Target: `None`)

## 5. Educational Concepts
### Arrow IPC Serialization Overhead
- **What is it:** The cost of serializing record batches and schema metadata into the Apache Arrow IPC stream format for inter-process or network transport.
- **Why it matters:** When a stream is split into many small frames that repeatedly re-encode the schema, serialization CPU overhead and payload size explode, choking shuffle performance.
- **Connection to Issue:** High-cardinality shuffles produce numerous small per-partition batches where per-frame schema re-serialization dominates the `send_time`.

### Partial Pre-Aggregation Ineffectiveness
- **What is it:** An optimization phase that aggregates rows locally before shuffling them across workers to reduce network transfer volume.
- **Why it matters:** If group key cardinality is nearly equal to the total row count, local aggregation yields virtually zero row reduction while adding unnecessary CPU hashing overhead.
- **Connection to Issue:** Running a partial AggregateExec on high-cardinality keys wastes CPU cycles on a hash pass and populates shuffles with unreduced row volumes.

