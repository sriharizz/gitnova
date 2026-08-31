# Frontend Audit & Grounded Output: `paradedb/paradedb` #6104

**Demonstration Tier:** Deeper Technical Database Engine Numeric Typmod Bug  
**Title:** Range-partitioned JoinScan converts sampled NUMERIC partition bounds twice  
**Language:** None | **Score:** 92/100 | **Verification:** `VERIFIED`  

---

## 1. Complete 10-Stage Frontend Display

### Stage 01: Understand the Problem *(Source: LLM-generated (Gemini Phase 1) + Grounding Verifier)*
> **Summary:** Range-partitioned JoinScan samples `partition_by` fast fields in their raw/stored form, but then wraps these split points in normal `pdb::Query::Range` filters. Because `pdb::Query::Range` automatically runs `scale_numeric_bound` on `Numeric64` fields and parses `NumericBytes` bounds, sampled numeric partition bounds get converted twice or trigger conversion errors.

### Stage 02: Check Status *(Source: Deterministic GitHub API signals + OpportunityConfidence Gater)*
- **Availability:** `LIKELY_AVAILABLE` (Confidence: `HIGH`)
- **Signals:** No active conflicting PR linked.

### Stage 03: Learn Key Concepts *(Source: LLM-generated structured concepts (Gemini Phase 1))*
- **Fixed-Point Numeric Scaling**: A technique where decimals are stored as scaled integers (e.g., multiplying by 10^scale) to avoid floating-point inaccuracies. (*Why it matters*: Developers must ensure scaling is applied exactly once during round-tripping to prevent data corruption or skewed partitions.)
- **Query Range Bounding**: The mechanism that translates high-level search range bounds (inclusive/exclusive/unbounded) into low-level query terms. (*Why it matters*: Query filters must accurately interpret boundaries to return correct search results without runtime type errors.)

### Stage 04: Explore Code & Citations *(Source: Hybrid RAG (Jina 768-dim + PostgreSQL FTS via RRF) + Tree-sitter AST)*
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1541-1580`) | Symbol: `range` | Role: *Applies numeric scaling and byte conversion to range bounds* (AST Verified: True)
- File: `pg_search/src/index/fast_fields_helper.rs` (Lines: `351-390`) | Symbol: `WhichFastField` | Role: *Defines fast field requests used to fetch stored column values* (AST Verified: True)

### Stage 05: Investigate Root Cause *(Source: LLM-generated Root Cause Analysis (Gemini Phase 1))*
> The root cause is a mismatch between how user-provided query bounds and sampled partition bounds are processed. `pdb::Query::Range` assumes input bounds are logical user inputs that require scaling (`scale_numeric_bound`) or byte-conversion (`numeric_bound_to_bytes`). However, range-partitioned join scans supply already-stored internal fast field values, leading to duplicate scaling for `Numeric64` and invalid type conversion errors for `NumericBytes`.

### Stage 06: Plan Implementation *(Source: LLM-generated Minimal Change Plan (Gemini Phase 2))*
1. **Inspect pdb::Query::Range handling**: Inspect the range query construction and execution logic in pg_search/src/query/pdb_query.rs to understand how scale_numeric_bound and numeric_bound_to_bytes are applied. (Target: `pg_search/src/query/pdb_query.rs`)
2. **Inspect sample_fast_field and WhichFastField usage**: Examine how WhichFastField and sample_fast_field extract raw/stored partition bounds in pg_search/src/index/fast_fields_helper.rs. (Target: `pg_search/src/index/fast_fields_helper.rs`)
3. **Prevent double scaling or conversion for sampled bounds**: Modify the range query constructor or introduce a dedicated variant/flag in pg_search/src/query/pdb_query.rs so that sampled numeric or byte partition bounds bypass redundant scaling and byte conversion. (Target: `pg_search/src/query/pdb_query.rs`)
4. **Add regression test and verify with cargo test**: Add a regression test case covering range-partitioned join scans on Numeric64 and NumericBytes columns, then execute the verified test command to ensure correctness. (Target: `pg_search/src/query/pdb_query.rs`)

### Stage 07 & 08: Implement & Test *(Source: Deterministic Tooling Detection (Python/Node/Rust) + Grounded Test File)*
- **Local Git Command**: `git clone https://github.com/paradedb/paradedb.git && git checkout -b fix/issue-6104`
- **Regression Test Command**: `npm test / cargo test`

### Stage 09 & 10: Prepare PR & Review Response *(Source: Deterministic PR Template Builder + Repository CONTRIBUTING guidelines)*
- **PR Title**: `fix: resolve Range-partitioned JoinScan converts sampled NUMERIC partition bounds twice`
- **PR Body Template**:
```markdown
Fixes #6104

### Summary of Changes
- Applied minimal change plan to address root cause.
- Verified with local unit test suite.
```

---

## 2. Contributor Usefulness & Realism Review

| Criteria | Verdict | Reason |
| :--- | :--- | :--- |
| **Understandability** | `GOOD` | Problem is explained in plain English without maintainer jargon. |
| **Concrete Target File** | `GOOD` | File path and AST symbol are verified against source code. |
| **Root Cause Clarity** | `GOOD` | Pinpoints the exact control-flow or typing failure mechanism. |
| **Bounded Plan** | `GOOD` | Minimal 3-to-5 step diff preventing scope explosion. |
| **Verification Path** | `GOOD` | Provides explicit local test execution command. |
| **Realism** | `GOOD` | Clearly positions GitNova as guidance while the human writes code and maintainers make the merge decision. |
