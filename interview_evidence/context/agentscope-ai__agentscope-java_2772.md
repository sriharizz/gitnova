# Issue Context Dossier: `agentscope-ai/agentscope-java` #2772

**Title:** [Bug]:非沙箱模式下,分布式部署机器workspace使用共享磁盘挂载会导致.skill-cache竞争  
**Repository:** https://github.com/agentscope-ai/agentscope-java  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> In distributed non-sandbox deployments using shared disk mounts, multiple concurrent user requests accessing the same workspace path experience file race conditions and `NoSuchFileException` errors due to a global, shared `.skills-cache` directory.

## 2. Root Cause Analysis
> In `ReActAgent` and associated dynamic skill middleware components, the working directory and `.skills-cache` are resolved to a common shared path on the mounted disk. When concurrent requests execute `stage()` and trigger `garbageCollectOrphans`, one request deletes files out from underneath another concurrent request's `Files.walk` traversal.

## 3. Grounded Code Locations & Citations
- File: `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java` (Lines: `4446-4485`) | Symbol: `Builder` | Role: *Relevant Code* (Verified: True)
- File: `agentscope-core/src/main/java/io/agentscope/core/agent/RuntimeContext.java` (Lines: `316-355`) | Symbol: `RuntimeContext` | Role: *Relevant Code* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect RuntimeContext and ReActAgent workspace resolution**: Examine agentscope-core/src/main/java/io/agentscope/core/agent/RuntimeContext.java and agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java to understand how workspace paths and the global .skills-cache directory are currently resolved and shared across concurrent requests. (Target: `agentscope-core/src/main/java/io/agentscope/core/agent/RuntimeContext.java`)
2. **Incorporate session or user identifiers into skill cache paths**: Modify workspace and skill cache path resolution logic in RuntimeContext or ReActAgent to namespace the .skills-cache directory per user or session identifier, preventing concurrent file race conditions on shared storage. (Target: `agentscope-core/src/main/java/io/agentscope/core/agent/RuntimeContext.java`)
3. **Safeguard file cleanup and traversal operations**: Review garbageCollectOrphans and deleteRecursively usages to handle NoSuchFileException robustly during concurrent file traversals in shared disk mount environments. (Target: `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java`)
4. **Add concurrency regression test and execute verification**: Implement a multi-threaded regression test simulating concurrent user requests accessing workspace skill staging to ensure no NoSuchFileException is thrown, then execute the test suite. (Target: `None`)

## 5. Educational Concepts
### File System Race Condition
- **What is it:** A concurrency bug where two or more threads or processes try to read, modify, or delete the same file or directory at the same time.
- **Why it matters:** Unsynchronized file operations on shared storage lead to unpredictable failures like missing files when one thread deletes an item being traversed by another.
- **Connection to Issue:** Concurrent user requests attempt to garbage-collect and materialize skills in a shared `.skills-cache` directory, causing a race condition and `NoSuchFileException`.

### Resource Namespacing
- **What is it:** Isolating shared resources by appending unique identifiers (such as user IDs or session IDs) to resource paths or keys.
- **Why it matters:** Prevents data collision and interference between different tenants or users sharing the same physical storage infrastructure.
- **Connection to Issue:** Isolating the skill cache path per user (using `userId`) prevents separate user requests from competing over the exact same `.skills-cache` directory.

