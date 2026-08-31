# Issue Context Dossier: `alibaba/nacos` #15708

**Title:** nacos-client 3.2.3: sun.misc.Unsafe::allocateMemory warning from shaded Netty still reproduces on JDK 25  
**Repository:** https://github.com/alibaba/nacos  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The nacos-client library shades gRPC and Netty dependencies. On JDK 25, Netty's internal PlatformDependent0 class attempts to use sun.misc.Unsafe::allocateMemory for off-heap memory allocation, which triggers a terminal deprecation warning on startup.

## 2. Root Cause Analysis
> The root cause is that the shaded version of Netty (packaged inside nacos-client via gRPC shading) uses sun.misc.Unsafe::allocateMemory for direct memory access/allocation. In JDK 25, this method is terminally deprecated, causing the JVM to emit a warning when it is accessed. Since the dependency is shaded inside nacos-client, the warning points directly to the nacos-client JAR. Note that the exact pom.xml or shading configuration files are INSUFFICIENT_EVIDENCE in the retrieved codebase chunks.

## 3. Grounded Code Locations & Citations
- *General repository target scope*

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Shaded Dependencies**: Inspect the root pom.xml and client/pom.xml to identify the exact versions of io.grpc and io.netty being shaded into the nacos-client artifact. (Target: `pom.xml`)
2. **Upgrade Shaded Netty/gRPC Versions**: Upgrade the shaded io.grpc and io.netty dependencies to versions that support JDK 25 and avoid using terminally deprecated sun.misc.Unsafe methods, or configure the system property 'io.netty.noUnsafe=true' during client initialization. (Target: `client/pom.xml`)
3. **Verify Warning Absence on JDK 25**: Run the nacos-client initialization code on JDK 25 and verify that no terminal deprecation warnings regarding sun.misc.Unsafe::allocateMemory are printed to standard error. (Target: `None`)

## 5. Educational Concepts
### Dependency Shading
- **What is it:** Shading is the process of renaming and packaging a dependency (and its transitive dependencies) inside another jar file to avoid classpath conflicts.
- **Why it matters:** It allows library developers to bundle specific versions of third-party libraries (like Netty or gRPC) without forcing the users of the library to use those exact same versions in their own applications.
- **Connection to Issue:** The warning comes from com.alibaba.nacos.shaded.io.grpc.netty..., which is a shaded version of Netty bundled inside nacos-client. To fix the warning, Nacos must upgrade the underlying dependency that is being shaded.

### Java Unsafe API Deprecation
- **What is it:** The sun.misc.Unsafe class provides low-level, unsafe mechanisms (like direct off-heap memory allocation) that bypass JVM safety checks. Modern JDK versions (like JDK 25) are terminally deprecating and removing these APIs.
- **Why it matters:** Developers must transition away from sun.misc.Unsafe to ensure their applications remain compatible with future Java releases and do not crash or emit warnings on startup.
- **Connection to Issue:** Netty's PlatformDependent0 class uses Unsafe::allocateMemory for high-performance off-heap buffer allocation. On JDK 25, this triggers a terminal deprecation warning, requiring an upgrade to a Netty version that uses modern JDK APIs or handles the deprecation gracefully.

