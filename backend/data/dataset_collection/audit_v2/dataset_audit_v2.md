# GitNova Dataset Audit Report (v2)

**Audit Date**: 2026-08-17T16:43:30.651513+00:00  
**Dataset Assessed**: `gitnova_raw_issues_v1.jsonl`

---

## 1. Population Overview

| Category | Count | Percentage |
| :--- | :--- | :--- |
| **Total Raw GitHub Records** | **650** | 100.0% |
| **Pull Requests (`is_pull_request: true`)** | **392** | 60.31% |
| **Real GitHub Issues (`is_pull_request: false`)** | **258** | 39.69% |

> [!IMPORTANT]
> **Audit Finding**: Out of 650 raw records collected in v1, **258 are genuine GitHub issues**, while **392 are Pull Requests**.
> Because our target for candidate relevance fine-tuning is **500–700 REAL ISSUES**, we must collect an additional **~350 real issues** to reach our target.

---

## 2. Issue Type Distribution (Real Issues)

| Issue Type | Count | Share (%) |
| :--- | :--- | :--- |
| **bug** | 84 | 32.56% |
| **enhancement** | 70 | 27.13% |
| **other** | 26 | 10.08% |
| **build/CI** | 22 | 8.53% |
| **documentation** | 15 | 5.81% |
| **UI** | 13 | 5.04% |
| **question** | 10 | 3.88% |
| **testing** | 9 | 3.49% |
| **dependency** | 4 | 1.55% |
| **RFC/proposal** | 2 | 0.78% |
| **security** | 1 | 0.39% |
| **refactor** | 1 | 0.39% |
| **performance** | 1 | 0.39% |

---

## 3. Real Issues Language Distribution

| Language | Real Issues | Share (%) |
| :--- | :--- | :--- |
| **Kotlin** | 31 | 12.0% |
| **Go** | 24 | 9.3% |
| **Java** | 22 | 8.5% |
| **JavaScript** | 20 | 7.8% |
| **PHP** | 17 | 6.6% |
| **Dart** | 16 | 6.2% |
| **Shell** | 16 | 6.2% |
| **Python** | 13 | 5.0% |
| **Solidity** | 12 | 4.7% |
| **TypeScript** | 12 | 4.7% |
| **Rust** | 11 | 4.3% |
| **Scala** | 11 | 4.3% |
| **C++** | 9 | 3.5% |
| **Haskell** | 9 | 3.5% |
| **templ** | 9 | 3.5% |
| **C#** | 8 | 3.1% |
| **Ruby** | 7 | 2.7% |
| **JSON** | 5 | 1.9% |
| **C** | 4 | 1.6% |
| **Dockerfile** | 2 | 0.8% |

---

## 4. Content Quality & Freshness

- **Average Body Word Count**: 207.3 words
- **Median Body Word Count**: 101 words
- **Short Issues (<20 words)**: 32 (12.4%)
- **Long Issues (>500 words)**: 25 (9.69%)
- **Missing Bodies**: 10
- **Missing Titles**: 0
- **Issues with Comments**: 131 (50.78%)
- **Oldest Issue**: `2020-01-27T16:10:23Z`
- **Newest Issue**: `2026-08-17T16:04:18Z`

---

## 5. Audit Decision

**Decision**: **`COLLECT_MORE_ISSUES`**  
*(Proceed to Phase 2 to collect additional real issues until total real issues reach 550–650).*
