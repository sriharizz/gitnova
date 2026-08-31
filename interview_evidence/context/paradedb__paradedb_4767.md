# Issue Context Dossier: `paradedb/paradedb` #4767

**Title:** Better error message for queries without a where clause  
**Repository:** https://github.com/paradedb/paradedb  
**Language:** Rust  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When users execute queries that invoke a ParadeDB function (such as `pdb.score` or `pdb.snippet`) in the SELECT clause without a corresponding WHERE clause operator (like `@@@`), ParadeDB currently throws a generic and unhelpful error: `ERROR: Unsupported query shape. Please report at https://github.com/paradedb/paradedb/issues/new/choose`. This issue requests a clearer, more user-friendly error message communicating that a WHERE clause operator is required.

## 2. Root Cause Analysis
> ParadeDB relies on PostgreSQL query rewriting and Planner/Executor hooks where search functions in the SELECT clause expect the query structure to be driven or bound by a search operator in the WHERE clause (e.g. using `@@@`). When the WHERE clause operator is omitted, the internal query shape classifier fails to match any valid execution path, falling through to a catch-all unsupported query shape error.

## 3. Grounded Code Locations & Citations
- File: `pg_search/src/api/builder_fns/pdb.rs` (Lines: `141-180`) | Symbol: `parse_query` | Role: *Defines builder functions for query construction.* (Verified: True)
- File: `pg_search/src/api/builder_fns/paradedb.rs` (Lines: `106-145`) | Symbol: `term_with_operator` | Role: *Handles term operator bindings used in query pushdown and evaluation.* (Verified: True)
- File: `pg_search/src/query/pdb_query.rs` (Lines: `1-40`) | Symbol: `Query` | Role: *Defines query variants and structures for search execution.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect query shape validation and builder functions**: Examine parse_query in pg_search/src/api/builder_fns/pdb.rs and query shape handling in pg_search/src/query/pdb_query.rs to understand how unsupported query shapes are currently caught and where pdb scoring/snippet functions are processed without a WHERE clause operator. (Target: `pg_search/src/api/builder_fns/pdb.rs`)
2. **Identify catch-all error handling for unsupported query shapes**: Locate the exact code path returning 'Unsupported query shape' when a SELECT clause invokes a `pdb.` scoring or snippet function without a corresponding WHERE clause operator. (Target: `pg_search/src/query/pdb_query.rs`)
3. **Implement clear and descriptive error messaging**: Modify the error handling logic in pg_search/src/query/pdb_query.rs or pdb.rs to check if `pdb.` functions are used without a WHERE clause operator, replacing the generic error with a specific message stating that a WHERE clause operator is required. (Target: `pg_search/src/query/pdb_query.rs`)
4. **Add regression test and execute verification suite**: Add a test case executing a `pdb.score` or `pdb.snippet` function in the SELECT clause without a WHERE clause operator, asserting that the new descriptive error message is returned correctly. (Target: `pg_search/src/api/builder_fns/pdb.rs`)

## 5. Educational Concepts
### PostgreSQL Query Pushdown & Planner Hooks
- **What is it:** A mechanism by which PostgreSQL delegates parts of query execution or expression rewriting to custom extensions.
- **Why it matters:** Understanding how custom search functions interact with PostgreSQL query planning helps developers pinpoint where unsupported query structures are intercepted.
- **Connection to Issue:** Explains why queries missing a WHERE clause operator fail during planning or execution rather than returning an intuitive error message.

### User-Facing Error Validation
- **What is it:** The practice of validating user inputs or query shapes early and throwing descriptive, actionable error messages instead of generic crash or panic messages.
- **Why it matters:** Clear error messages dramatically improve developer experience by guiding users toward correct SQL syntax.
- **Connection to Issue:** The goal of this issue is to replace the generic 'Unsupported query shape' error with a precise validation message explaining the missing WHERE clause requirement.

