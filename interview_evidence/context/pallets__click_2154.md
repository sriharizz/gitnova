# Issue Context Dossier: `pallets/click` #2154

**Title:** xdg-open zombie process remains by default in WSL2 after click.launch()  
**Repository:** https://github.com/pallets/click  
**Language:** Python  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When using `click.launch()` in Windows Subsystem for Linux 2 (WSL2) to open a URL or file, a zombie (defunct) process for `xdg-open` is left behind in the process table. This happens because `click.launch()` spawns `xdg-open` as a background process using `subprocess.Popen` and immediately returns without waiting for it to finish (when `wait=False`, which is the default). Because the parent Python process does not reap the terminated child process, the operating system keeps it in the process table as a zombie until the parent Python process exits. The issue can be resolved by updating the documentation to warn users about this WSL2 behavior and advise setting `wait=True` to avoid zombie processes.

## 2. Root Cause Analysis
> In `src/click/_termui_impl.py`, the `open_url` function handles Linux/BSD platforms by executing `c = subprocess.Popen(["xdg-open", url])`. When `wait` is `False` (the default), the function immediately returns `0` without calling `c.wait()`. On Unix-like operating systems (including WSL2), when a child process terminates, it remains in the process table as a 'zombie' until its parent process reads its exit status via a system call like `waitpid()`. Because Click does not call `wait()` or otherwise reap the child process when `wait=False`, the zombie `xdg-open` process persists until the parent Python process exits.

## 3. Grounded Code Locations & Citations
- File: `src/click/termui.py` (Lines: `902-928`) | Symbol: `launch` | Role: *Public API definition and documentation of the wait parameter* (Verified: True)
- File: `src/click/_termui_impl.py` (Lines: `785-852`) | Symbol: `open_url` | Role: *Implementation of URL launching using subprocess.Popen and xdg-open* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect launch function docstring**: Inspect the `launch` function definition and its docstring in `src/click/termui.py` to locate the description of the `wait` parameter. (Target: `src/click/termui.py`)
2. **Update docstring with WSL2 warning**: Update the docstring of the `launch` function in `src/click/termui.py` to add a warning note about WSL2/Linux environments where `wait=False` (the default) can result in zombie `xdg-open` processes, recommending `wait=True` for long-running parent processes. (Target: `src/click/termui.py`)
3. **Verify test suite execution**: Run the existing test suite to ensure that no syntax errors or regressions were introduced by the docstring update. (Target: `tests/test_termui.py`)

## 5. Educational Concepts
### Zombie Processes (Defunct Processes)
- **What is it:** A zombie process is a completed process that still has an entry in the operating system's process table. This entry is kept so the parent process can read the child's exit status.
- **Why it matters:** If a parent process runs for a long time and repeatedly spawns child processes without reaping them (reading their exit status), the process table can fill up, preventing new processes from being created.
- **Connection to Issue:** In WSL2, `xdg-open` exits quickly but remains as a zombie because Click's `open_url` spawns it with `subprocess.Popen` and does not call `.wait()` or `.poll()` when `wait=False`.

### Process Reaping in Python
- **What is it:** Process reaping is the act of collecting the exit status of a terminated child process, which allows the operating system to completely remove it from the process table. In Python, this is typically done by calling `.wait()` or `.poll()` on a `subprocess.Popen` object.
- **Why it matters:** Developers must manage the lifecycle of spawned subprocesses to avoid resource leaks (like zombie processes) in long-running applications.
- **Connection to Issue:** Setting `wait=True` in `click.launch()` forces Click to call `c.wait()`, which reaps the `xdg-open` process and prevents it from becoming a zombie.

