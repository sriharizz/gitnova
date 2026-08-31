# Issue Context Dossier: `scikit-learn/scikit-learn` #34744

**Title:** BUG: Two ProgressBar on the same estimator raises a KeyErr  
**Repository:** https://github.com/scikit-learn/scikit-learn  
**Language:** Python  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Attaching multiple instances of the same callback (such as two ProgressBar instances) to an estimator causes a KeyError during teardown because multiple callback instances try to access and pop the same shared root UUID from global queues/monitors.

## 2. Root Cause Analysis
> Callbacks such as ProgressBar rely on global dictionaries (`_run_queues`, `_run_monitors`) keyed by `context.root_uuid`. When two identical callback instances are executed, the first one pops the key successfully during teardown, leaving the key missing when the second callback instance attempts to pop it, causing a KeyError.

## 3. Grounded Code Locations & Citations
- File: `sklearn/callback/_base.py` (Lines: `8-43`) | Symbol: `_BaseCallback` | Role: *Defines the base callback protocol including setup and teardown hooks.* (Verified: True)
- File: `sklearn/callback/_base.py` (Lines: `47-121`) | Symbol: `FitCallback` | Role: *Defines the fit task callback hooks protocol.* (Verified: True)
- File: `sklearn/callback/_base.py` (Lines: `125-139`) | Symbol: `AutoPropagatedCallback` | Role: *Defines auto-propagated callback protocol attributes.* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect global queue management in callbacks**: Inspect symbol AutoPropagatedCallback and FitCallback in sklearn/callback/_base.py to understand how `context.root_uuid` is used to manage teardown and global dictionary cleanup. (Target: `sklearn/callback/_base.py`)
2. **Guard global state popping against KeyError**: Modify the teardown or cleanup logic in sklearn/callback/_base.py where global dictionaries like `_run_queues` and `_run_monitors` are popped using `context.root_uuid`, using `.pop(key, None)` instead of direct dictionary pop/removal to prevent KeyError when duplicate callback instances clean up the same root UUID. (Target: `sklearn/callback/_base.py`)
3. **Add regression test for multiple identical callbacks**: Add a new test case in the callback test suite that attaches multiple instances of the same callback (e.g. two ProgressBar instances) to an estimator and calls fit(), verifying that no KeyError is raised during teardown. (Target: `sklearn/tests/test_callback.py`)
4. **Run test suite verification**: Run pytest on the callback module to ensure the fix resolves the KeyError and does not introduce regressions. (Target: `None`)

## 5. Educational Concepts
### Callback Lifecycle Management
- **What is it:** The sequence of setup, execution hooks, and teardown methods invoked during an estimator's training process.
- **Why it matters:** Ensures resources like threads, monitors, and progress bars are correctly initialized before training begins and properly cleaned up when training finishes.
- **Connection to Issue:** The issue arises because two separate ProgressBar instances attempt to clean up global resources using the same root UUID during teardown, causing a collision.

### Global State Collision
- **What is it:** A bug pattern where multiple independent components attempt to read, write, or delete items from a shared global dictionary or resource.
- **Why it matters:** Shared global state can lead to race conditions, unexpected deletions, and KeyErrors when multiple instances assume exclusive access.
- **Connection to Issue:** ProgressBar uses module-level global dictionaries (`_run_queues`, `_run_monitors`) keyed by session UUIDs, which fail when duplicate callback instances execute.

