# Issue Context Dossier: `agentscope-ai/agentscope-java` #2787

**Title:** [Bug]:MarketplaceStager orphan GC races with concurrent staging —UncheckedIOException(NoSuchFileException) escapes and fails the whole agent call  
**Repository:** https://github.com/agentscope-ai/agentscope-java  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When multiple agent calls share a workspace root with different visible skills, concurrent orphan garbage collection in MarketplaceStager can delete files out from under an active directory traversal. This throws a NoSuchFileException wrapped in an UncheckedIOException, escaping the try-catch block and terminating the entire agent execution.

## 2. Root Cause Analysis
> Garbage collection methods like garbageCollectOrphans(), deleteRecursively(), and removeUnexpected() catch checked IOException but fail to catch RuntimeException / UncheckedIOException thrown by lazy stream traversal when files disappear concurrently. Additionally, garbage collection is executed outside the protective try-catch boundaries of individual skill staging.

## 3. Grounded Code Locations & Citations
- File: `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java` (Lines: `1-40`) | Symbol: `ReActAgent` | Role: *Core agent class referencing skills and middlewares* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect MarketplaceStager traversal and error boundaries**: Inspect the directory traversal and file deletion logic in MarketplaceStager and ReActAgent.java to locate where Files.walk or recursive deletion streams throw UncheckedIOException due to concurrent file disappearance. (Target: `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java`)
2. **Catch UncheckedIOException and NoSuchFileException**: Wrap directory traversal and cleanup actions (such as garbageCollectOrphans(), deleteRecursively(), and removeUnexpected()) in robust try-catch blocks or stream operators that gracefully catch UncheckedIOException and NoSuchFileException when concurrently modified paths vanish. (Target: `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java`)
3. **Ensure safe protection boundaries around skill staging**: Verify that individual skill staging and concurrent workspace root operations are protected from unexpected runtime exceptions, ensuring orphan cleanups do not terminate agent execution. (Target: `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java`)
4. **Add regression test for concurrent skill staging and workspace garbage collection**: Implement a regression test simulating concurrent agent calls sharing a workspace root with differing visible skills to ensure no NoSuchFileException or UncheckedIOException escapes during orphan garbage collection. (Target: `agentscope-core/src/test/java/io/agentscope/core/ReActAgentTest.java`)
5. **Run test suite verification**: Run the repository test command to verify that all agent executions complete successfully under concurrent workspace modifications. (Target: `None`)

## 5. Educational Concepts
### Unchecked IOException in Java Streams
- **What is it:** Java NIO file streams like Files.walk() throw runtime UncheckedIOException when an underlying file or directory is deleted mid-traversal.
- **Why it matters:** Developers must catch runtime exceptions around NIO streams when working in concurrent or multi-threaded environments where files can change unexpectedly.
- **Connection to Issue:** Catching UncheckedIOException during directory walking and orphan cleanup prevents abrupt agent failure when concurrent calls modify shared cache directories.

### Resource Isolation and Concurrency Safety
- **What is it:** Ensuring multiple concurrent tasks do not interfere with shared resources through proper scoping, locking, or fault tolerance.
- **Why it matters:** Shared filesystem resources in multi-user applications are vulnerable to race conditions if caching and cleanup mechanisms are not designed for concurrency.
- **Connection to Issue:** The issue stems from shared cache garbage collection across concurrent agent calls with different skill visibilities.

