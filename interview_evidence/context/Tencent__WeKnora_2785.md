# Issue Context Dossier: `Tencent/WeKnora` #2785

**Title:** [Feature]: 为问答FAQ 知识库列表增加排序功能  
**Repository:** https://github.com/Tencent/WeKnora  
**Language:** Go  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The feature request asks to add sorting functionality to the Q&A FAQ knowledge base entry list in the Tencent/WeKnora repository, supporting creation time, update time, and name fields with ascending/descending order toggle.

## 2. Root Cause Analysis
> The backend handler and service methods currently only accept basic sorting parameters (e.g., `sort_order` defaulting or checking for `asc`) and do not process query parameters for sorting field selection (such as creation time, update time, or name) and direction.

## 3. Grounded Code Locations & Citations
- File: `internal/handler/faq.go` (Lines: `36-75`) | Symbol: `ListEntries` | Role: *API handler parsing query parameters for FAQ entries listing* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect ListEntries Handler**: Examine ListEntries in internal/handler/faq.go to understand existing query parameter binding, sorting parameters, and service call conventions. (Target: `internal/handler/faq.go`)
2. **Update Query Parameters for Sorting**: Modify the query parameter binding struct in internal/handler/faq.go to accept sorting field options (creation time, update time, name) and direction options (asc/desc). (Target: `internal/handler/faq.go`)
3. **Update Service Layer and SQL Query Generation**: Pass the new sorting field and direction parameters down to the FAQ repository/service layer to build the correct ORDER BY clause dynamically. (Target: `internal/handler/faq.go`)
4. **Add Regression Test**: Add or update test cases in the handler and service tests to verify correct sorting behavior for creation time, update time, and name fields in both ascending and descending order. (Target: `internal/handler/embed_flow_test.go`)
5. **Run Test Suite**: Execute the package tests to verify the sorting feature implementation and ensure no regressions are introduced. (Target: `None`)

## 5. Educational Concepts
### API Query Parameter Binding
- **What is it:** The process of extracting and validating HTTP query parameters sent by a client in a web request.
- **Why it matters:** Developers need to parse user-supplied filters and sorting options safely to customize database queries.
- **Connection to Issue:** Adding sorting fields and order requires capturing new query parameters from the client request in `ListEntries`.

### Database Sorting and Pagination
- **What is it:** Ordering database query results by specific columns in ascending or descending order alongside pagination limits.
- **Why it matters:** Enables users to efficiently organize and locate records when dealing with large datasets.
- **Connection to Issue:** The core feature requires extending the database query and service layer to sort by creation time, update time, or name.

