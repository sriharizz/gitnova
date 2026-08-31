# Issue Context Dossier: `expo/expo` #49449

**Title:** [dom-components] Android release APK ships www.bundle source maps (cloneable MRE)  
**Repository:** https://github.com/expo/expo  
**Language:** TypeScript  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> When building a release Android app using Expo DOM components, Metro generates native Hermes sourcemaps which inadvertently cause Expo DOM embedding to generate and ship www.bundle source map files inside android_asset, bloating the final APK release. The issue can be resolved by respecting the includeSourceMaps configuration flag inside getFilesFromSerialAssets so that source map files are not persistently written when source maps are disabled or unrequested for store builds.

## 2. Root Cause Analysis
> The root cause stems from exportEmbedAsync setting includeSourceMaps based on the native sourcemap URL for DOM exports. During Android release builds, sourcemapOutput is set for Hermes, causing Metro to emit maps. However, downstream in serialization and persistence (getFilesFromSerialAssets), the includeSourceMaps flag is ignored, leading to map persistence regardless of configuration.

## 3. Grounded Code Locations & Citations
- File: `packages/expo-dev-client/metro.config.js` (Lines: `1-14`) | Symbol: `config` | Role: *Metro configuration example showing custom transformer and resolver settings* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect exportEmbedAsync and getFilesFromSerialAssets Control Flow**: Inspect exportEmbedAsync and getFilesFromSerialAssets to examine how the includeSourceMaps flag is currently passed and where source map files are unconditionally written to android_asset. (Target: `packages/expo-dom/src/exportEmbedAsync.ts`)
2. **Update getFilesFromSerialAssets to Respect includeSourceMaps**: Modify getFilesFromSerialAssets to conditionally filter out and skip persisting source map files when the includeSourceMaps parameter evaluates to false. (Target: `packages/expo-dom/src/exportEmbedAsync.ts`)
3. **Add Unit Tests for Source Map Exclusion**: Add or update unit tests for exportEmbedAsync and getFilesFromSerialAssets to verify that when includeSourceMaps is false, no .map or www.bundle source map files are emitted to assets. (Target: `packages/expo-dom/src/__tests__/exportEmbedAsync-test.ts`)
4. **Run Test Suite to Validate Fix**: Execute the repository test command to ensure the fix passes existing test suites and introduces no regressions. (Target: `None`)

## 5. Educational Concepts
### Source Maps in Production Builds
- **What is it:** Source maps map minified production code back to original source code for debugging, but are typically excluded from production release packages to save space and protect source code privacy.
- **Why it matters:** Shipping source maps in production mobile application binaries (like APKs) can massively inflate file sizes and expose internal source code.
- **Connection to Issue:** Expo DOM components currently leak www.bundle .map files into Android release APKs because sourcemap persistence is unconditionally triggered during Android release builds.

### Configuration Flag Propagation
- **What is it:** Ensuring that user-facing configuration options or build flags (like includeSourceMaps) are correctly passed down and honored through every layer of a build or serialization pipeline.
- **Why it matters:** If intermediate pipeline functions ignore configuration parameters, user settings fail to take effect, leading to unexpected runtime or build behavior.
- **Connection to Issue:** The core bug occurs because getFilesFromSerialAssets receives the includeSourceMaps flag but fails to evaluate it before persisting bundle maps.

