# GitNova Raw Issues Dataset (v1.0.0)

## Overview
This dataset contains **650 raw, un-filtered GitHub issues** collected across **60 repositories** spanning **20 programming languages**.

It is purpose-built as the foundational evidence corpus for the future **GitNova Candidate-Relevance Fine-Tuning Experiment**.

> [!IMPORTANT]
> **Zero Label Policy**: This dataset contains **NO PRE-LABELS** (`label`, `label_source`, and `label_confidence` are strictly `null`).
> Independent annotations (`HIGH_FIT`, `MEDIUM_FIT`, `LOW_FIT`) will be applied in subsequent offline labeling phases via GPT-5.6 Luna and Gemini Flash.

---

## Dataset Summary Statistics
- **Total Raw Issues**: 650
- **Unique Repositories**: 60
- **Unique Languages**: 20
- **Pull Requests (Tracked via `is_pull_request`)**: 392 (60.31%)
- **Issues with Discussion Comments**: 313 (48.15%)
- **Average Body Word Count**: 247.7 words (Median: 150 words)

---

## Language Distribution
| Language | Issue Count | Share (%) |
| :--- | :--- | :--- |
| **C++** | 60 | 9.2% |
| **Java** | 60 | 9.2% |
| **Go** | 55 | 8.5% |
| **JavaScript** | 52 | 8.0% |
| **Python** | 51 | 7.8% |
| **Rust** | 51 | 7.8% |
| **Kotlin** | 49 | 7.5% |
| **Ruby** | 49 | 7.5% |
| **TypeScript** | 48 | 7.4% |
| **Dart** | 42 | 6.5% |
| **PHP** | 24 | 3.7% |
| **Shell** | 24 | 3.7% |
| **C** | 12 | 1.8% |
| **C#** | 12 | 1.8% |
| **Haskell** | 12 | 1.8% |
| **JSON** | 12 | 1.8% |
| **Scala** | 12 | 1.8% |
| **Solidity** | 12 | 1.8% |
| **templ** | 9 | 1.4% |
| **Dockerfile** | 4 | 0.6% |

---

## Top Repositories
| Repository | Language | Issue Count |
| :--- | :--- | :--- |
| `curl/curl` | - | 12 |
| `babalae/better-genshin-impact` | - | 12 |
| `alibaba/zvec` | - | 12 |
| `spf13/cobra` | - | 12 |
| `Nike-Inc/hal` | - | 12 |
| `openstreetmap/id-tagging-schema` | - | 12 |
| `alibaba/nacos` | - | 12 |
| `expressjs/express` | - | 12 |
| `eclipse-apoapsis/ort-server` | - | 12 |
| `spiral/framework` | - | 12 |
| `pallets/click` | - | 12 |
| `Homebrew/homebrew-cask` | - | 12 |
| `sharkdp/bat` | - | 12 |
| `plokhotnyuk/jsoniter-scala` | - | 12 |
| `jenkinsci/bom` | - | 12 |
| `MIgHTy-alIeN/MEV-Ethereum-Trading-Bot` | - | 12 |
| `facebook/docusaurus` | - | 12 |
| `apache/trafficserver` | - | 12 |
| `ente/ente` | - | 12 |
| `kubescape/kubescape` | - | 12 |

---

## Schema Reference

### 1. Identity
- `dataset_id`: Unique identifier (`gn_raw_...`)
- `repo_id`: Database repository UUID
- `repo_name`: Repository slug (`owner/repo`)
- `owner`: Repository owner login
- `repo_url`: GitHub repository URL
- `issue_number`: Issue number on GitHub
- `issue_url`: GitHub issue HTML URL

### 2. Issue Content
- `title`: Raw issue title
- `body`: Raw issue markdown body
- `labels`: List of normalized label objects (`name`, `color`, `description`)
- `issue_state`: `"open"` or `"closed"`
- `created_at`, `updated_at`, `closed_at`: ISO timestamp strings
- `author_login`: Issue author username
- `comments_count`: Total comments count on GitHub

### 3. Discussion
- `comments`: Array of raw comment text strings
- `comment_authors`: Array of comment author logins
- `comment_timestamps`: Array of comment ISO timestamps

### 4. Repository Context
- `repo_language`: Primary language
- `repo_languages`: List of languages
- `repo_topics`: Repository topics
- `repo_stars`: Stargazer count
- `repo_forks`: Fork count

### 5. Pipeline Observation Fields (Reference Only — NOT Labels)
- `existing_prefilter_decision`: GitNova deterministic gate outcome (`PASS` or `DROP`)
- `existing_prefilter_reason`: Rule description if dropped
- `existing_publication_status`: Status in Supabase `issues` table
- `existing_difficulty`: Tier in Supabase (`BEGINNER`, `BEGINNER_PLUS`, `INTERMEDIATE`, `ADVANCED`)

### 6. Future Annotation Fields
- `label`: `null` (To be populated offline)
- `label_source`: `null`
- `label_confidence`: `null`
