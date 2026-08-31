# Issue Context Dossier: `pallets/click` #3802

**Title:** `KeyboardInterrupt` during `click.prompt()` can race  
**Repository:** https://github.com/pallets/click  
**Language:** Python  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When a user presses Ctrl-C (sending a KeyboardInterrupt) during a click prompt or stream check, Click may fail to catch or handle it cleanly under certain timing conditions, leading to an unhandled KeyboardInterrupt exception.

## 2. Root Cause Analysis
> In Python, `KeyboardInterrupt` and `SystemExit` inherit from `BaseException`, not `Exception`. In `CliRunner.invoke()` and core execution flows, `except Exception as e:` catches standard errors but bypasses `BaseException`, letting `KeyboardInterrupt` propagate unhandled if raised asynchronously or during stream operations.

## 3. Grounded Code Locations & Citations
- File: `src/click/testing.py` (Lines: `630-720`) | Symbol: `CliRunner.invoke` | Role: *Catches standard Exception but does not catch BaseException like KeyboardInterrupt* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect CliRunner.invoke in src/click/testing.py**: Examine the exception handling logic within `CliRunner.invoke` in `src/click/testing.py` to identify where standard `Exception` blocks let `BaseException` or `KeyboardInterrupt` escape unhandled. (Target: `src/click/testing.py`)
2. **Extend exception handling to catch BaseException or KeyboardInterrupt**: Modify the invocation runner block in `src/click/testing.py` to explicitly catch `KeyboardInterrupt` or `BaseException` where appropriate, ensuring it is cleanly captured and recorded in runner results rather than causing an unhandled traceback crash. (Target: `src/click/testing.py`)
3. **Add regression test for KeyboardInterrupt in test suite**: Write a dedicated test case using `CliRunner` that simulates a `KeyboardInterrupt` during command invocation, asserting that the runner captures the exception or exits cleanly without an unhandled traceback crash. (Target: `src/click/testing.py`)
4. **Run pytest to verify the fix and regression test**: Execute the verified test suite command to ensure the new regression test passes successfully and that no existing tests are broken. (Target: `None`)

## 5. Educational Concepts
### BaseException vs Exception
- **What is it:** In Python, `Exception` is the base class for all ordinary errors, while `BaseException` is the root for system-exiting events like `SystemExit` and `KeyboardInterrupt`.
- **Why it matters:** Using `except Exception:` will accidentally miss `KeyboardInterrupt` and `SystemExit`, which can cause unexpected crashes when a user aborts via Ctrl-C.
- **Connection to Issue:** The race condition occurs because `KeyboardInterrupt` is a `BaseException` and bypasses standard `except Exception:` blocks in Click's invocation and stream runners.

### Exception Propagation in CLI Tools
- **What is it:** Command-line tools need to intercept user interruptions gracefully to print clean error messages instead of raw Python tracebacks.
- **Why it matters:** Raw tracebacks degrade the user experience and can break automated test runners expecting clean exit codes or structured abort messages.
- **Connection to Issue:** Fixing the issue requires ensuring that `KeyboardInterrupt` is properly caught and converted into a clean exit or handled abort.

