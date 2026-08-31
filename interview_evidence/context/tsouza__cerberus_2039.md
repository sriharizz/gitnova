# Issue Context Dossier: `tsouza/cerberus` #2039

**Title:** traceql: duration > span.<dynamic-int-attribute> answers where reference Tempo returns zero  
**Repository:** https://github.com/tsouza/cerberus  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> Comparing a TraceQL duration intrinsic against a dynamic attribute (such as `duration > span.child.index`) results in a live behavioral divergence between Cerberus and reference Tempo. While both correctly accept the query during static typing, Cerberus returns 100 traces whereas reference Tempo returns 0 traces because integer attributes should not satisfy duration-typed comparisons.

## 2. Root Cause Analysis
> The lowering logic or expression evaluator in TraceQL maps dynamic attribute fields without strictly checking whether the runtime value type matches the expected intrinsic type (duration), causing integer-typed attributes like child indices to be improperly evaluated against duration thresholds.

## 3. Grounded Code Locations & Citations
- File: `cmd/bench-report/e2e_chdb.go` (Lines: `70-85`) | Symbol: `emitTraceQL` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect TraceQL duration comparison logic**: Examine emitTraceQL in cmd/bench-report/e2e_chdb.go to understand how dynamic attributes and duration intrinsics are evaluated and lowered. (Target: `cmd/bench-report/e2e_chdb.go`)
2. **Enforce strict OTel value type checks for duration comparisons**: Modify the expression evaluation or lowering logic in cmd/bench-report/e2e_chdb.go to ensure dynamic attributes are strictly checked for duration compatibility rather than automatically coercing numeric attributes like integer indices. (Target: `cmd/bench-report/e2e_chdb.go`)
3. **Add regression test for non-duration dynamic attributes**: Update cmd/bench-report/e2e_chdb_test.go to include a test case verifying that comparing a duration intrinsic against a non-duration dynamic attribute (e.g., an integer attribute) correctly returns 0 traces instead of false matches. (Target: `cmd/bench-report/e2e_chdb_test.go`)
4. **Run test suite for verification**: Execute the test command to verify that the fix resolves the behavioral divergence and all tests pass successfully. (Target: `None`)

## 5. Educational Concepts
### TraceQL Dynamic Attributes
- **What is it:** Attributes whose types are not known statically at parse time and must be evaluated per-row.
- **Why it matters:** Understanding dynamic attributes is essential when handling queries where operands do not have fixed types upfront.
- **Connection to Issue:** The issue stems from how dynamic attributes like `span.child.index` are coerced during per-row evaluations against duration intrinsics.

### Behavioral Divergence and Compat Baselines
- **What is it:** Discrepancies between reference implementations (like Tempo) and custom engines (like Cerberus).
- **Why it matters:** Ensures that compatibility tests accurately reflect upstream expectations rather than silently absorbing incorrect matching behavior.
- **Connection to Issue:** The smoke test fixture was reverted from a real attribute to an empty attribute to avoid masking this lowering mismatch until root-caused.

