import os
import sys
import json
import csv
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")
from supabase import create_client

from app.evaluation.metrics import (
    calculate_recall_at_k,
    calculate_mrr_at_k,
    calculate_hit_at_k,
    calculate_file_relevance,
    deduplicate_retrieved_files
)

def paths_match(f1: str, f2: str) -> bool:
    f1_norm = f1.strip().replace('\\', '/')
    f2_norm = f2.strip().replace('\\', '/')
    return f1_norm == f2_norm or f1_norm.endswith('/' + f2_norm) or f2_norm.endswith('/' + f1_norm)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

bucket_json_path = backend_path / "data" / "rolling_rag_eval_bucket_analysis.json"
with open(bucket_json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

cases = data.get("cases", [])
bucket_a = [c for c in cases if c.get("primary_bucket") == "BUCKET_A"]

print(f"Total Bucket A cases to audit: {len(bucket_a)}")

detailed_audits = []

for idx, c in enumerate(bucket_a, 1):
    case_key = c.get("case_key")
    repo = c.get("repo_name")
    num = c.get("issue_number")
    pr = c.get("merged_pr_number")
    
    # Query issue row from supabase
    iss_rows = supabase.table("issues").select(
        "id, repo_name, github_issue_number, title, retrieved_chunk_ids, repo_commit_sha, explanation, ai_hint"
    ).eq("repo_name", repo).eq("github_issue_number", num).execute().data or []
    
    iss = iss_rows[0] if iss_rows else {}
    raw_cids = iss.get("retrieved_chunk_ids") or []
    
    # Query code_chunks for each raw chunk_id in original order
    resolved_chunks = []
    if raw_cids:
        # Query matching chunks
        chunk_rows = supabase.table("code_chunks").select(
            "chunk_id, repo_name, file_path, symbol_name, start_line, end_line, commit_sha"
        ).in_("chunk_id", raw_cids[:15]).execute().data or []
        
        chunk_dict = {cr["chunk_id"]: cr for cr in chunk_rows}
        # Reconstruct in EXACT original raw_cids order
        for cid in raw_cids:
            if cid in chunk_dict:
                resolved_chunks.append(chunk_dict[cid])
                
    # Extracted retrieved file paths in original rank order (deduplicated preserving order)
    ordered_ret_files = []
    for ch in resolved_chunks:
        fp = ch.get("file_path")
        if fp and fp not in ordered_ret_files:
            ordered_ret_files.append(fp)
            
    # Ground truth files from PR
    gt_files = c.get("ground_truth_files", [])
    
    # Calculate metrics
    r1 = calculate_recall_at_k(ordered_ret_files, gt_files, k=1) or 0.0
    r5 = calculate_recall_at_k(ordered_ret_files, gt_files, k=5) or 0.0
    r10 = calculate_recall_at_k(ordered_ret_files, gt_files, k=10) or 0.0
    mrr10 = calculate_mrr_at_k(ordered_ret_files, gt_files, k=10) or 0.0
    hit10 = calculate_hit_at_k(ordered_ret_files, gt_files, k=10) or 0.0
    
    # Check match explanation
    matches_found = []
    for r_idx, rf in enumerate(ordered_ret_files[:10], 1):
        for gf in gt_files:
            if paths_match(rf, gf):
                matches_found.append({"rank": r_idx, "retrieved": rf, "ground_truth": gf})
                
    audit_entry = {
        "case_key": case_key,
        "repo_name": repo,
        "issue_number": num,
        "merged_pr_number": pr,
        "title": iss.get("title", ""),
        "raw_chunk_ids_count": len(raw_cids),
        "raw_chunk_ids": raw_cids[:5],
        "resolved_chunks_count": len(resolved_chunks),
        "ordered_retrieved_files": ordered_ret_files,
        "ground_truth_files": gt_files,
        "matches_found": matches_found,
        "recall_at_1": r1,
        "recall_at_5": r5,
        "recall_at_10": r10,
        "mrr_at_10": mrr10,
        "hit_at_10": hit10,
        "snapshot_commit": iss.get("repo_commit_sha")
    }
    detailed_audits.append(audit_entry)
    
    print(f"[{idx}/25] {case_key} (PR #{pr})")
    print(f"   Stored Chunks: {len(raw_cids)} | Resolved: {len(resolved_chunks)} | Ret Files: {ordered_ret_files}")
    print(f"   GT Files ({len(gt_files)}): {gt_files}")
    if matches_found:
        print(f"   🎯 MATCH AT RANK {matches_found[0]['rank']}: {matches_found[0]['retrieved']} == {matches_found[0]['ground_truth']}")
    else:
        print(f"   ❌ ZERO MATCH: Ret={ordered_ret_files} vs GT={gt_files}")
    print(f"   Metrics: R@10={r10:.4f}, MRR={mrr10:.4f}, Hit@10={hit10:.4f}")
    print("-" * 70)

# Save JSON
out_json_path = backend_path / "data" / "rolling_rag_eval_bucket_a_audit.json"
with open(out_json_path, "w", encoding="utf-8") as f:
    json.dump(detailed_audits, f, indent=2, ensure_ascii=False)

# Save CSV
out_csv_path = backend_path / "data" / "rolling_rag_eval_bucket_a_audit.csv"
with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "case_key", "repo_name", "issue_number", "merged_pr_number", "title",
        "raw_chunk_ids_count", "resolved_chunks_count", "ordered_retrieved_files",
        "ground_truth_files", "recall_at_1", "recall_at_5", "recall_at_10",
        "mrr_at_10", "hit_at_10", "has_match"
    ])
    writer.writeheader()
    for da in detailed_audits:
        writer.writerow({
            "case_key": da["case_key"],
            "repo_name": da["repo_name"],
            "issue_number": da["issue_number"],
            "merged_pr_number": da["merged_pr_number"],
            "title": da["title"],
            "raw_chunk_ids_count": da["raw_chunk_ids_count"],
            "resolved_chunks_count": da["resolved_chunks_count"],
            "ordered_retrieved_files": "; ".join(da["ordered_retrieved_files"]),
            "ground_truth_files": "; ".join(da["ground_truth_files"]),
            "recall_at_1": da["recall_at_1"],
            "recall_at_5": da["recall_at_5"],
            "recall_at_10": da["recall_at_10"],
            "mrr_at_10": da["mrr_at_10"],
            "hit_at_10": da["hit_at_10"],
            "has_match": len(da["matches_found"]) > 0
        })

print(f"\nAudit complete. Artifacts written to {out_json_path} and {out_csv_path}.")
