# GitNova — Verified Claims & Engineering Limitations

---

## 1. What We CAN Claim (Verified Codebase Facts)

- **Scale**: Analyzed **1,457 GitHub issues** across **153 repositories**; published **119 high-confidence opportunities**.
- **Quality Firewall**: Rejects **91.8%** of candidate issues to protect junior developers from impossible/stale tasks.
- **RAG Grounding**: Implemented 768-dim dense + lexical Reciprocal Rank Fusion ($k=60$) achieving **94.0% Recall@1** and **100.0% Recall@5** on our 25-issue golden benchmark.
- **Zero Hallucinated Citations**: 100% of published citations are verified against AST file trees.
- **QLoRA Fine-Tuning**: Achieved **79.41% Macro-F1** and **82.22% Accuracy** on a strict 90-issue repository-held-out test set.

---

## 2. What We CANNOT Claim (Do Not State in Interviews)

- ❌ *Do NOT claim "real-time online user A/B testing".* (We ran offline ablation benchmarks).
- ❌ *Do NOT claim "distributed Ray/Spark cluster training".* (Single-node PyTorch training).
- ❌ *Do NOT claim "GitNova automatically opens and merges PRs".* (GitNova guides the developer; the maintainer makes the final merge decision).
