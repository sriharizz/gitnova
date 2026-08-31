import os
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

p = Path("c:/gitNova/backend/data/rolling_rag_eval_dataset.json")
with open(p, "r", encoding="utf-8") as f:
    cases = json.load(f)

print(f"Total Longitudinal Dataset Cases: {len(cases)}")

hits = [c for c in cases if c["metrics"]["hit_at_10"] > 0]
print(f"Total Cases with Ground-Truth Hits in Longitudinal Run: {len(hits)}")

for h in hits:
    ck = h["case_key"]
    pr = h["merged_pr_number"]
    ret = h["original_retrieval"]["retrieved_file_paths"]
    gt = h["ground_truth"]["files"]
    m = h["metrics"]
    print(f"🎯 Hit: {ck} (PR #{pr})")
    print(f"   Retrieved: {ret}")
    print(f"   Ground Truth: {gt}")
    print(f"   Recall@1: {m['recall_at_1']}, Recall@10: {m['recall_at_10']}, MRR@10: {m['mrr_at_10']}")
    print("-" * 60)
