# Issue Context Dossier: `nexu-io/open-design` #7249

**Title:** [Bug]: DSH on Windows: PowerShell loses media CLI stdout  
**Repository:** https://github.com/nexu-io/open-design  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> On Windows, running the Open Design media CLI via DeepSeek Harness and direct PowerShell invocation ($result = & $env:OD_NODE_BIN $env:OD_BIN media generate ...) fails to capture standard output, leaving $result empty ($null) and preventing agents from obtaining the task ID or status.

## 2. Root Cause Analysis
> The CLI help documentation in apps/daemon/src/cli.ts provides bash-specific commands and examples for the generate-wait loop but lacks equivalent verified guidance or wrapper handling for PowerShell on Windows, where direct ampersand invocation drops stdout streams under certain harness runtimes.

## 3. Grounded Code Locations & Citations
- File: `apps/daemon/src/cli.ts` (Lines: `1611-1650`) | Symbol: `runMedia` | Role: *Media CLI entry point and help routing* (Verified: True)
- File: `apps/daemon/src/cli.ts` (Lines: `2171-2210`) | Symbol: `printMediaHelp` | Role: *Media CLI help text containing POSIX bash example contract* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect printMediaHelp symbol in apps/daemon/src/cli.ts**: Inspect the printMediaHelp function and surrounding help text in apps/daemon/src/cli.ts to locate existing POSIX bash documentation and identify where PowerShell-specific invocation examples should be inserted. (Target: `apps/daemon/src/cli.ts`)
2. **Add PowerShell invocation documentation and examples**: Update printMediaHelp in apps/daemon/src/cli.ts to include clear Windows PowerShell instructions and examples using Start-Process or redirection patterns to ensure agents can successfully capture stdout. (Target: `apps/daemon/src/cli.ts`)
3. **Verify CLI help output generation**: Verify that running the media CLI help command correctly displays the new PowerShell instructions alongside the existing bash examples without formatting regressions. (Target: `apps/daemon/src/cli.ts`)
4. **Run test suite verification**: Run the repository test command to ensure all existing CLI tests pass successfully and verify the documentation updates. (Target: `apps/daemon/src/cli.ts`)

## 5. Educational Concepts
### PowerShell Output Redirection
- **What is it:** How Windows PowerShell handles standard output streams and command execution compared to bash.
- **Why it matters:** Developers and automated agents need to know how to reliably capture stdout and stderr streams when executing CLI tools inside PowerShell environments.
- **Connection to Issue:** The issue stems from PowerShell dropping or failing to capture standard output when using direct ampersand execution (&), requiring alternative patterns like Start-Process.

### CLI Help Contract Documentation
- **What is it:** Maintaining clear, accurate usage instructions and code examples within application command-line interfaces.
- **Why it matters:** AI coding agents and human developers rely directly on CLI help text to understand how to interact with automation endpoints.
- **Connection to Issue:** Updating the help text in apps/daemon/src/cli.ts will guide DeepSeek Harness agents on Windows to use the correct PowerShell workaround pattern.

