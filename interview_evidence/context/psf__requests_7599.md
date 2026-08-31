# Issue Context Dossier: `psf/requests` #7599

**Title:** Documentation for stream parameter is ambiguous  
**Repository:** https://github.com/psf/requests  
**Language:** Python  
**Suitability Score:** 96/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The docstring for the `stream` parameter in `Session.request` is misleading. It suggests that setting `stream=False` (the default) prevents immediate downloading of the response content, whereas the actual runtime behavior is the exact opposite: `stream=False` immediately downloads the content, and `stream=True` defers it.

## 2. Root Cause Analysis
> In `src/requests/sessions.py`, the `Session.send` method executes `if not stream: r.content` to immediately download the response body when `stream` is `False`. However, the docstring for `Session.request` was written as `:param stream: (optional) whether to immediately download the response content. Defaults to False.`. This phrasing is ambiguous and suggests that the default value of `False` disables immediate downloading, which contradicts the actual control flow.

## 3. Grounded Code Locations & Citations
- File: `src/requests/sessions.py` (Lines: `554-556`) | Symbol: `Session.request` | Role: *Contains the ambiguous docstring for the stream parameter* (Verified: True)
- File: `src/requests/sessions.py` (Lines: `799-801`) | Symbol: `Session.send` | Role: *Implements the actual runtime behavior where not streaming triggers immediate download* (Verified: True)
- File: `src/requests/api.py` (Lines: `54-55`) | Symbol: `request` | Role: *Contains the correct docstring description for the stream parameter as a reference* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect the stream parameter docstring and runtime behavior**: Inspect the `Session.request` docstring in `src/requests/sessions.py` and compare it with the actual runtime behavior in `Session.send` where `if not stream: r.content` is called, as well as the docstring in `src/requests/api.py`. (Target: `src/requests/sessions.py`)
2. **Update the Session.request docstring**: Modify the docstring for the `stream` parameter in `Session.request` in `src/requests/sessions.py` to clarify that setting it to `True` defers downloading the response content, whereas the default `False` downloads it immediately. (Target: `src/requests/sessions.py`)
3. **Verify docstring consistency and run tests**: Verify that the updated docstring is clear and consistent with `src/requests/api.py`. Run the test suite using `pytest` to ensure no syntax or documentation build issues are introduced. (Target: `tests/test_requests.py`)

## 5. Educational Concepts
### Response Streaming
- **What is it:** A technique in HTTP clients where the response body is not immediately read into memory, allowing the developer to consume the response content in chunks or at a later time.
- **Why it matters:** It is crucial for handling large files or continuous data streams without consuming excessive system memory or causing out-of-memory errors.
- **Connection to Issue:** The `stream` parameter controls this behavior in Requests. The docstring incorrectly described the default state of this parameter, leading to developer confusion about when content is downloaded.

### API Documentation Accuracy
- **What is it:** Ensuring that the docstrings and public API documentation precisely match the actual runtime behavior of the code.
- **Why it matters:** Inaccurate documentation leads to developer confusion, integration bugs, and unnecessary issues being opened, even if the underlying code functions perfectly.
- **Connection to Issue:** This issue is a pure documentation bug where the docstring's description of the `stream` parameter contradicts the actual runtime behavior of the `Session.request` method.

