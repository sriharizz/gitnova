# Issue Context Dossier: `psf/requests` #7443

**Title:** mypy warns about invalid types for json argument  
**Repository:** https://github.com/psf/requests  
**Language:** Python  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> Mypy raises type-checking errors when passing JSON-serializable dictionaries to the `json` argument of requests methods if those dictionaries are first assigned to intermediate variables. This happens because mypy infers overly broad types (like `dict[str, Collection[str]]` or `dict[str, object]`) for the intermediate variables, which are incompatible with the strict `JsonType` definition in requests.

## 2. Root Cause Analysis
> When a user constructs a dictionary with mixed value types and assigns it to an intermediate variable without an explicit type annotation, mypy infers its type based on the least common supertype of its values. For example, `{"foo": d, "bar": "hi"}` (where `d: dict[str, str]`) is inferred as `dict[str, Collection[str]]` because both `dict` and `str` implement the `Collection` protocol. Similarly, `{"foo": d, "bool": True}` is inferred as `dict[str, object]`. When this intermediate variable is passed to the `json` argument, mypy compares the inferred type against `_t.JsonType`. Because `_t.JsonType` is defined as a strict recursive type or a union that does not include `Collection[str]` or `object`, mypy raises an incompatible type error. In contrast, passing the dictionary literal directly works because mypy can use contextual typing to check each element individually against `JsonType` without inferring a broad intermediate type.

## 3. Grounded Code Locations & Citations
- File: `src/requests/_types.py` (Lines: `38-39`) | Symbol: `JsonType` | Role: *Type definition file where JsonType is defined* (Verified: True)
- File: `src/requests/api.py` (Lines: `117-134`) | Symbol: `post` | Role: *API function defining the post method with json parameter* (Verified: True)
- File: `src/requests/models.py` (Lines: `284-375`) | Symbol: `Request` | Role: *Model class representing a Request with json attribute and parameter* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect JsonType definition in src/requests/_types.py**: Examine the current definition of `JsonType` in `src/requests/_types.py` to understand how it restricts types and why it rejects inferred types like `dict[str, Any]` or `dict[str, object]`. (Target: `src/requests/_types.py`)
2. **Broaden JsonType definition**: Modify `JsonType` in `src/requests/_types.py` to be `Any` or a broader union (e.g., `Any`) to allow intermediate variables with inferred types to be passed to the `json` parameter without mypy errors. (Target: `src/requests/_types.py`)
3. **Verify type annotations in api.py and models.py**: Check that `requests.api.request`, `requests.sessions.Session.request`, and `requests.models.Request` use the updated `JsonType` or `Any` for their `json` parameters. (Target: `src/requests/api.py`)
4. **Add type-checking regression test**: Create a type-checking test case (e.g., using mypy or in a dedicated type test file) that assigns a mixed-type dictionary to an intermediate variable and passes it to `requests.post(..., json=data)` to ensure no type-checking errors are raised. (Target: `tests/test_requests.py`)
5. **Run tests and linter**: Run the test suite using pytest and run mypy/pre-commit to verify that the type-checking passes and no regressions are introduced. (Target: `None`)

## 5. Educational Concepts
### Recursive Type Definitions vs. Type Inference Limitations
- **What is it:** Recursive types define a type in terms of itself (e.g., a JSON dict contains keys mapping to JSON values, which can themselves be JSON dicts). While mathematically elegant, type checkers like mypy struggle with them because they infer intermediate variables as broader types (like object or Collection) which do not match the recursive definition.
- **Why it matters:** Understanding the limitations of recursive type definitions helps developers design type stubs and annotations that are both useful and practical, avoiding false-positive type errors for library users.
- **Connection to Issue:** The strict recursive definition of `JsonType` in `_types.py` causes mypy to reject valid JSON-serializable dictionaries when they are assigned to intermediate variables and their types are inferred as `dict[str, object]`.

### Contextual Typing (Bidirectional Type Inference)
- **What is it:** Contextual typing is when a type checker uses the expected type of an expression to help infer its actual type. For example, passing a dictionary literal directly to a function parameter typed as `JsonType` allows mypy to type-check each element of the literal individually.
- **Why it matters:** It explains why `requests.post(..., json={"foo": d})` works perfectly, while assigning the dictionary to an intermediate variable `j = {"foo": d}` first and then passing `j` fails.
- **Connection to Issue:** Explains the reproduction steps where direct literals work but intermediate variables fail, highlighting why the type definition itself needs to be more permissive (e.g., using `Any`) to support intermediate variables.

