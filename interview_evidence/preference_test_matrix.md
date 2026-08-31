# GitNova — Read-Only Preference Test Matrix Results

**Tested Against:** 121 Live Published Opportunities in Supabase  

| Test Scenario | Input Filter | Matches Found | Repositories Returned | Languages Returned |
| :--- | :--- | :--- | :--- | :--- |
| **Case A (Python Only)** | `python` (BEGINNER) | **15** | deepset-ai/haystack, pallets/click, psf/requests, scikit-learn/scikit-learn, unslothai/unsloth | `Python` |
| **Case B (TypeScript Only)** | `typescript` (BEGINNER) | **19** | MoonshotAI/kimi-code, expo/expo, facebook/docusaurus, nexu-io/open-design | `TypeScript` |
| **Case C (Python + Beginner)** | `python` (BEGINNER) | **15** | deepset-ai/haystack, pallets/click, psf/requests, scikit-learn/scikit-learn, unslothai/unsloth | `Python` |
| **Case D (Rust Only)** | `rust` (BEGINNER) | **19** | edison7009/EchoBird, openai/codex, paradedb/paradedb, sharkdp/bat, sinelaw/fresh | `Rust` |
| **Case E (Go Only)** | `go` (BEGINNER) | **25** | elastic/elastic-package, fullsend-ai/fullsend, k0sproject/k0s, kubescape/kubescape, multica-ai/multica | `Go` |
| **Case F (Java Only)** | `java` (BEGINNER) | **10** | agentscope-ai/agentscope-java, alibaba/nacos, kestra-io/kestra, microcks/microcks | `Java` |
| **Case G (All Tiers / Multi-Language)** | `python, typescript, rust, go` (ALL) | **88** | MikeLuu99/metasearch-rust, MoonshotAI/kimi-code, Tencent/WeKnora, deepset-ai/haystack, edison7009/EchoBird | `Go, Python, Rust, TypeScript` |

---

## Key Observation for Interviewers
When a user filters for `Python`, only Python issues (e.g. `pallets/click`, `unslothai/unsloth`) are returned. When filtering for `Rust`, only Rust repositories (e.g. `sinelaw/fresh`, `paradedb/paradedb`) appear. The preference filtering operates with **100% precision**.
