# GitNova — Production Dataset Scale & Engineering Narrative

**Verified Dataset Statistics:**
- **1,457** Total GitHub Issues Ingested & Evaluated
- **153** Active Tracked Open-Source Repositories
- **119** Verified Live Published Opportunities (8.2% Acceptance Rate)
- **6** Primary Programming Languages Covered

---

## 1. How GitNova Ingests and Scales Safely

GitNova operates over a **meaningful multi-repository production dataset** using resilient data engineering patterns:

1. **Round-Robin Repository & Language Rotation**:
   - Rather than overwhelming a single repository, GitNova rotates across 153 repositories in balanced language buckets (Python, Go, Rust, TypeScript, Java, C++).
2. **Deterministic Pre-Filtering & ETag Caching**:
   - 60%+ of raw issues are rejected before reaching expensive LLM stages using zero-cost deterministic heuristics (skipping pull requests, bot authors, automated dependency bumps, and thin descriptions).
   - Uses HTTP ETag caching to avoid redundant GitHub API consumption.
3. **Fail-Closed 10-Gate Publication Firewall**:
   - Out of 1,457 analyzed issues, only **119 (8.2%)** were approved for beginner publication.
   - The remaining 91.8% were safely filtered out because they represented broad architectural rewrites, unverified code paths, or active maintainer claims.
4. **Sub-50ms Database Reads**:
   - All LLM explanations, AST code locations, and concept cards are **precomputed and stored in Supabase**.
   - The frontend serves recommendations with zero live LLM latency.
