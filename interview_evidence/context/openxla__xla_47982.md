# Issue Context Dossier: `openxla/xla` #47982

**Title:** [GPU] SM107 compilation fails with CUDA 12.9 because sm_107a requires PTX 9.4  
**Repository:** https://github.com/openxla/xla  
**Language:** C++  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> Compilation fails on SM107 GPUs when using CUDA 12.9 because XLA selects PTX 8.8, whereas sm_107a requires PTX 9.4, causing an LLVM fatal error that terminates the process.

## 2. Root Cause Analysis
> A version mismatch exists between recent SM107 target support additions and the CUDA-to-PTX version mapping logic. Specifically, CUDA 12.9 maps to an older PTX version (8.8) by default, while the SM107 GPU target requires PTX version 9.4 or higher, leading to rejection by LLVM.

## 3. Grounded Code Locations & Citations
- File: `xla/core/host_offloading/host_offloading_nanort_executable.cc` (Lines: `71-110`) | Symbol: `HostOffloadingNanoRtExecutable` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect CUDA-to-PTX version mapping logic**: Inspect HostOffloadingNanoRtExecutable and related CUDA version mapping structures to understand how PTX versions are selected for target sm_107a under CUDA 12.9. (Target: `xla/core/host_offloading/host_offloading_nanort_executable.cc`)
2. **Update PTX version mapping for SM107 and CUDA 12.9**: Modify the version resolution logic to ensure that targeting sm_107a with CUDA 12.9 maps to at least PTX version 9.4 instead of 8.8, preventing the LLVM fatal error. (Target: `xla/core/host_offloading/host_offloading_nanort_executable.cc`)
3. **Add regression test for SM107 PTX version selection**: Add a new test case in xla/core/host_offloading/host_offloading_executable_test.cc to verify that compilation for sm_107a under CUDA 12.9 successfully resolves to PTX 9.4 without crashing. (Target: `xla/core/host_offloading/host_offloading_executable_test.cc`)
4. **Run test suite verification**: Run the host offloading executable tests to confirm the PTX version mapping fix resolves the crash and passes successfully. (Target: `xla/core/host_offloading/host_offloading_executable_test.cc`)

## 5. Educational Concepts
### PTX Version Mapping
- **What is it:** The translation version mapping between CUDA toolkit releases and the Parallel Thread Execution (PTX) instruction set version supported by LLVM for NVIDIA GPUs.
- **Why it matters:** Mismatches between CUDA driver/toolkit versions and PTX requirements result in hard compiler rejection errors from LLVM.
- **Connection to Issue:** CUDA 12.9 is currently mapped to PTX 8.8, but SM107 support (sm_107a) strictly requires PTX 9.4, triggering an LLVM fatal error.

### Recoverable Compilation Errors
- **What is it:** Handling compiler failures by returning a structured error status (such as absl::Status) to the caller instead of invoking hard process aborts.
- **Why it matters:** Hard process crashes break worker pools and make debugging or testing infrastructure unstable when individual compilation units fail.
- **Connection to Issue:** The issue notes that the compiler abort breaks worker pools and crashes tests; proper error handling should propagate a recoverable exception.

