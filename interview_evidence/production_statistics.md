# GitNova — Production Database Snapshot & Statistics

**Snapshot Date:** 2026-08-31T13:27:50.152710+00:00  
**Data Source:** Live Production Supabase PostgreSQL Instance  

---

## 1. High-Level Production Scale

| Metric | Verified Production Count | Interview Context |
| :--- | :--- | :--- |
| **Total Ingested Issues** | **1473** | Issues processed across automated pipeline discovery runs. |
| **Total Published Opportunities** | **121** | High-confidence opportunities that passed all 10 fail-closed gates. |
| **Active Repositories** | **153** | Actively tracked open-source projects in Supabase. |
| **Languages Represented** | **14** | Multi-language coverage (Python, Go, Rust, TypeScript, Java, etc.). |
| **Publication Acceptance Rate** | **8.21%** | **Key Highlight**: Strict 10-gate firewall rejects ~91.8% of noise/stale issues. |

---

## 2. Published Issues by Programming Language

| Language | Published Count | Percentage of Feed |
| :--- | :--- | :--- |
| **Go** | 28 | 23.1% |
| **Rust** | 22 | 18.2% |
| **TypeScript** | 20 | 16.5% |
| **Python** | 18 | 14.9% |
| **Java** | 10 | 8.3% |
| **C#** | 7 | 5.8% |
| **JSON** | 4 | 3.3% |
| **C++** | 3 | 2.5% |
| **JavaScript** | 2 | 1.7% |
| **Ruby** | 2 | 1.7% |
| **Kotlin** | 2 | 1.7% |
| **Other** | 1 | 0.8% |
| **Dart** | 1 | 0.8% |
| **C** | 1 | 0.8% |

---

## 3. Published Issues by Repository (Top Active)

| Repository | Published Issues Count |
| :--- | :--- |
| `MoonshotAI/kimi-code` | 10 |
| `fullsend-ai/fullsend` | 9 |
| `nexu-io/open-design` | 8 |
| `babalae/better-genshin-impact` | 7 |
| `paradedb/paradedb` | 7 |
| `openai/codex` | 7 |
| `pallets/click` | 6 |
| `psf/requests` | 5 |
| `unxed/f4` | 5 |
| `openstreetmap/id-tagging-schema` | 4 |
| `kestra-io/kestra` | 4 |
| `sinelaw/fresh` | 4 |
| `scikit-learn/scikit-learn` | 3 |
| `agentscope-ai/agentscope-java` | 3 |
| `unslothai/unsloth` | 3 |
| `k0sproject/k0s` | 3 |
| `multica-ai/multica` | 3 |
| `sharkdp/bat` | 2 |
| `expressjs/express` | 2 |
| `tsouza/cerberus` | 2 |
| `alibaba/nacos` | 2 |
| `mixxxdj/mixxx` | 2 |
| `clap-rs/clap` | 1 |
| `deepset-ai/haystack` | 1 |
| `spf13/cobra` | 1 |

---

## 4. Verification & Availability Status

- **Verification Status**: `{'VERIFIED': 121}` (100% AST Provenance checked)
- **Availability Status**: `{'LIKELY_AVAILABLE': 121}` (Guarantees no maintainer claim conflict)
- **Difficulty Tier**: `{'BEGINNER': 121}` (100% constrained to Beginner/Beginner-Plus)
