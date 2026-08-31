# Issue Context Dossier: `MikeLuu99/metasearch-rust` #5

**Title:** Feature Request: Optional API-backed Google engine (no HTML scraping)  
**Repository:** https://github.com/MikeLuu99/metasearch-rust  
**Language:** Rust  
**Suitability Score:** 76/100 (ContributionComplexity.INTERMEDIATE)  
**Availability Status:** `LIKELY_AVAILABLE`  

---

## 1. Problem Summary & Objective
> The repository currently implements HTML-scraping engines (DuckDuckGo, Brave, Startpage, Yahoo) that are prone to selector breakage and IP rate-limiting, alongside a fragile internal Google Images API. This issue proposes adding an optional, API-backed Google web search engine (using SerpBase) that activates only when an API key is provided via an environment variable, leaving existing behavior unchanged.

## 2. Root Cause Analysis
> The metasearch engine architecture relies on a `SearchEngine` trait implemented by individual engine modules and explicitly wired into `src/main.rs` and `src/engines/mod.rs`. Without a dedicated SerpBase engine implementation, module declaration, and conditional instantiation in `main.rs`, the API-backed Google option cannot participate in the aggregator RRF pipeline.

## 3. Grounded Code Locations & Citations
- File: `src/engines/mod.rs` (Lines: `1-40`) | Symbol: `SearchEngine` | Role: *Defines the SearchEngine trait implemented by search engines* (Verified: True)
- File: `src/main.rs` (Lines: `1-40`) | Symbol: `main` | Role: *Instantiates and registers search engines into the application vector* (Verified: True)

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect SearchEngine trait and existing engine implementations**: Examine the SearchEngine trait defined in src/engines/mod.rs and reference existing engine implementations such as startpage.rs to understand asynchronous request handling and response parsing conventions. (Target: `src/engines/mod.rs`)
2. **Implement the SerpBase engine module**: Create src/engines/serpbase.rs implementing the SearchEngine trait, fetching results from the SerpBase API when SERPBASE_API_KEY is present in the environment. (Target: `src/engines/serpbase.rs`)
3. **Register SerpBase engine in src/engines/mod.rs and src/main.rs**: Expose the serpbase module in src/engines/mod.rs and conditionally instantiate and push the SerpBase engine into the search engine vector in src/main.rs based on the SERPBASE_API_KEY environment variable. (Target: `src/main.rs`)
4. **Add integration and unit tests for SerpBase engine**: Add unit tests verifying that the SerpBase engine correctly handles missing API keys without error and successfully parses mock API responses when configured. (Target: `src/engines/serpbase.rs`)
5. **Execute test suite**: Run cargo test to verify that all existing engines and the new SerpBase engine pass successfully without regressions. (Target: `None`)

## 5. Educational Concepts
### The SearchEngine Trait Pattern
- **What is it:** A Rust trait defining a common interface (name and async search method returning a list of search results) that allows different search backends to be treated uniformly.
- **Why it matters:** It decouples the core aggregation logic from specific search providers, making it trivial to plug in new search backends.
- **Connection to Issue:** Implementing a new SerpBase engine requires adhering to this exact trait so it can be seamlessly passed into `query_all_engines()`.

### Optional Feature Activation via Environment Variables
- **What is it:** Conditional initialization of features based on whether required configuration secrets or API keys are present in the environment.
- **Why it matters:** Allows third-party API integrations to remain completely optional, preserving self-hosted privacy and preventing crashes when keys are missing.
- **Connection to Issue:** The SerpBase engine should only be instantiated and added to the engine fan-out if `SERPBASE_API_KEY` is set.

