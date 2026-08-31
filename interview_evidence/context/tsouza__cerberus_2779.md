# Issue Context Dossier: `tsouza/cerberus` #2779

**Title:** Stamp max_bytes_before_external_join as a join spill guardrail (chopt join_spill)  
**Repository:** https://github.com/tsouza/cerberus  
**Language:** Go  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Cerberus currently stamps max_bytes_before_external_group_by and max_bytes_before_external_sort on data-plane queries, but lacks a corresponding spill setting for joins. This causes heavy join queries to hit memory limits and trigger destructive code-241 OOM aborts instead of spilling to disk. The fix introduces the `join_spill` chopt feature to register and stamp `max_bytes_before_external_join = cap/2` on join-bearing queries.

## 2. Root Cause Analysis
> ClickHouse requires explicit memory thresholds to trigger external spilling for hash joins. Because Cerberus previously only configured external memory limits for GROUP BY and ORDER BY operations, large hash builds in join plans exceeded memory ceilings without an intermediate spill mechanism, resulting in hard server-side OOM aborts.

## 3. Grounded Code Locations & Citations
- File: `internal/chclient/client.go` (Lines: `1296-1335`) | Symbol: `MaxQueryMemoryBytes` | Role: *Provides MaxQueryMemoryBytes to size memory-related query settings relative to the client-wide cap.* (Verified: True)
- File: `internal/chclient/breaker.go` (Lines: `351-390`) | Symbol: `` | Role: *Handles code-241 memory rejections and circuit breaker exceptions.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect spill settings configuration**: Inspect internal/engine/spill.go to understand how applySpillSettings applies max_bytes_before_external_group_by and max_bytes_before_external_sort relative to MaxQueryMemoryBytes. (Target: `internal/engine/spill.go`)
2. **Implement join_spill chopt feature and join memory capping**: Add the join_spill chopt feature flag and update applySpillSettings to configure max_bytes_before_external_join = cap/2 alongside group_by and sort settings. (Target: `internal/engine/spill.go`)
3. **Verify query client integration**: Inspect internal/chclient/client.go to ensure MaxQueryMemoryBytes correctly passes the memory budget down to the engine spill configuration builder. (Target: `internal/chclient/client.go`)
4. **Add regression tests and execute verification suite**: Add test assertions in internal/chclient/drain_byte_budget_test.go verifying that join-bearing queries successfully stamp max_bytes_before_external_join when join_spill is enabled, then run go test ./... (Target: `internal/chclient/drain_byte_budget_test.go`)

## 5. Educational Concepts
### Database Query Spill Settings
- **What is it:** Configuration flags that instruct a database engine to write intermediate data to disk when memory usage exceeds a specific threshold.
- **Why it matters:** Without spill settings, memory-intensive operations like large joins or aggregations cause hard out-of-memory errors and crash or abort queries.
- **Connection to Issue:** This issue directly adds `max_bytes_before_external_join` to prevent costly join OOMs by enabling disk spilling.

### Client-Side Query Plan Stamping
- **What is it:** The practice of injecting server configuration settings into database client requests based on the shape and requirements of the query plan.
- **Why it matters:** It ensures that specific query types receive tuned runtime limits (like memory caps and spill triggers) dynamically before execution.
- **Connection to Issue:** Cerberus uses query plan stamping to attach settings rules like group_by/sort spill caps, and this fix extends that exact pattern to join operations.

