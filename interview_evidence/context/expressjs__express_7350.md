# Issue Context Dossier: `expressjs/express` #7350

**Title:** res.render()/app.render() throws opaque TypeError for a view name ending in "."  
**Repository:** https://github.com/expressjs/express  
**Language:** JavaScript  
**Suitability Score:** 67/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> When a view name ends with a dot (e.g., 'index.'), path.extname() returns '.' which is truthy. This causes Express to skip its default engine fallback mechanism, leaving the extension as '.' and attempting to call require('') when loading the view module, resulting in a synchronous TypeError.

## 2. Root Cause Analysis
> The View constructor in `lib/view.js` uses `path.extname(name)` to determine if an extension was explicitly provided. For a string like `'index.'`, `path.extname()` returns `'.'` instead of an empty string or a valid extension. Express interprets this truthy single-dot extension as valid, fails to find a matching template engine for `'.'`, tries to load module `''`, and throws a Node.js runtime TypeError.

## 3. Grounded Code Locations & Citations
- File: `lib/view.js` (Lines: `36-75`) | Symbol: `View` | Role: *Initializes View extension and handles default engine fallback logic where extname('.') incorrectly triggers valid extension handling.* (Verified: True)
- File: `lib/view.js` (Lines: `71-110`) | Symbol: `View` | Role: *Loads template engine using `this.ext.slice(1)`, which evaluates to `''` when `this.ext` is `'.'`, causing `require('')`.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect View extension logic in lib/view.js**: Inspect the constructor of View in lib/view.js where path.extname(name) is used to check for an extension, and observe how a trailing dot results in ext equal to '.' which bypasses the default engine fallback check (!this.ext). (Target: `lib/view.js`)
2. **Validate extension string in View constructor**: Modify the extension assignment or check in lib/view.js so that if path.extname(name) results in exactly '.', it is treated as an empty string (no extension) rather than a valid extension. (Target: `lib/view.js`)
3. **Ensure fallback handles trailing dot view names correctly**: Verify that when ext is normalized or ignored when it equals '.', the default engine lookup triggers correctly and leads to a graceful 'Failed to lookup view' error callback instead of throwing a synchronous TypeError. (Target: `lib/view.js`)
4. **Add regression test for view names ending with a dot**: Add a new test case in the test suite (e.g., within view-related tests) that attempts to render or lookup a view with a trailing dot (e.g. 'index.') and asserts that it passes an error to the callback instead of throwing a synchronous TypeError. (Target: `test/res.render.js`)
5. **Run test suite to verify fix**: Run the repository test command to ensure the regression test passes and no existing view rendering tests are broken. (Target: `None`)

## 5. Educational Concepts
### Path Extension Parsing Edge Cases
- **What is it:** Handling special characters and edge cases (like trailing dots) when using `path.extname()`.
- **Why it matters:** Functions like `path.extname()` can return unexpected results on malformed input strings, which can corrupt subsequent control flow if not properly validated.
- **Connection to Issue:** A trailing dot causes `path.extname()` to return `'.'` rather than an empty string, tricking Express into thinking a file extension was supplied.

### Defensive Module Loading Validation
- **What is it:** Validating dynamic module names before passing them to the Node.js `require()` function.
- **Why it matters:** Passing empty or invalid strings to `require()` throws synchronous runtime errors that can bypass error-handling callbacks and crash applications.
- **Connection to Issue:** Express attempts to `require(mod)` where `mod` is an empty string derived from `this.ext.slice(1)`, resulting in a synchronous TypeError instead of invoking the callback with an error.

