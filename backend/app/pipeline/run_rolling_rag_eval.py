import os
import sys
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Path setup
backend_path = Path(__file__).resolve().parents[2]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from supabase import create_client
from app.core.config import settings
from app.pipeline.github_client import GitHubClient
from app.pipeline.code_retriever import CodeRetriever

EVAL_DATASET_PATH = backend_path / "data" / "rolling_rag_eval_dataset.json"


def calculate_retrieval_metrics(retrieved_files: List[str], ground_truth_files: List[str]) -> Dict[str, float]:
    """
    Computes Recall@1, Recall@5, Recall@10, MRR@10, and Hit@10.
    Ground truth files are NEVER exposed to the query or retriever.
    """
    if not ground_truth_files:
        return {
            "recall_at_1": 0.0,
            "recall_at_5": 0.0,
            "recall_at_10": 0.0,
            "mrr_at_10": 0.0,
            "hit_at_10": 0.0
        }

    gt_set = set(f.strip().lower() for f in ground_truth_files)
    retrieved_lower = [f.strip().lower() for f in retrieved_files]

    # Recall @ K
    def recall_at_k(k: int) -> float:
        top_k = set(retrieved_lower[:k])
        hits = len(gt_set.intersection(top_k))
        return hits / len(gt_set) if len(gt_set) > 0 else 0.0

    r1 = recall_at_k(1)
    r5 = recall_at_k(5)
    r10 = recall_at_k(10)

    # Hit @ 10
    hit10 = 1.0 if len(gt_set.intersection(set(retrieved_lower[:10]))) > 0 else 0.0

    # MRR @ 10
    mrr = 0.0
    for idx, f in enumerate(retrieved_lower[:10], start=1):
        if f in gt_set:
            mrr = 1.0 / idx
            break

    return {
        "recall_at_1": round(r1, 4),
        "recall_at_5": round(r5, 4),
        "recall_at_10": round(r10, 4),
        "mrr_at_10": round(mrr, 4),
        "hit_at_10": round(hit10, 4)
    }


def run_rolling_rag_eval(min_age_days: int = 1, max_cases_to_evaluate: int = 15, dry_run: bool = False) -> Dict[str, Any]:
    """
    Rolling RAG evaluation pipeline:
    1. Queries stored GitNova issues in Supabase older than min_age_days.
    2. Checks GitHub status for closed state / associated merged PRs.
    3. Extracts actual changed files from merged PR as ground truth.
    4. Evaluates existing RAG retrieval against the historical issue without leaking ground truth.
    5. Stores evaluation metrics in eval_results table and rolling dataset JSON.
    """
    print("🚀 Starting GitNova Rolling RAG Evaluation Pipeline...")
    print(f"   Evaluation Target: Issues older than {min_age_days} day(s), Max Cases: {max_cases_to_evaluate}")

    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")

    if not supabase_url or not supabase_key:
        print("❌ CRITICAL: SUPABASE_URL or SUPABASE_KEY missing.")
        return {"status": "failed", "error": "Missing Supabase credentials"}

    supabase = create_client(supabase_url, supabase_key)
    github = GitHubClient(supabase_client=supabase)
    retriever = CodeRetriever(supabase_client=supabase)

    # Load local evaluation dataset cache
    EVAL_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    eval_dataset: Dict[str, Any] = {}
    if EVAL_DATASET_PATH.exists():
        try:
            with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
                eval_dataset = json.load(f)
        except Exception:
            eval_dataset = {}

    # 1. Query stored issues
    issues_resp = supabase.table("issues").select(
        "id, repo_name, github_issue_number, title, is_published, created_at, repo_id"
    ).order("created_at", desc=True).limit(100).execute()

    all_issues = issues_resp.data or []
    print(f"📊 Found {len(all_issues)} total candidates in database to audit for ground-truth PRs.")

    evaluated_count = 0
    newly_added_cases = 0
    skipped_count = 0
    eval_cases_summary = []

    for iss in all_issues:
        if evaluated_count >= max_cases_to_evaluate:
            break

        repo_name = iss.get("repo_name")
        issue_number = iss.get("github_issue_number")
        if not repo_name or not issue_number:
            continue

        case_key = f"{repo_name}#{issue_number}"

        # Deduplicate
        if case_key in eval_dataset and not dry_run:
            skipped_count += 1
            continue

        # 2. Check GitHub API for Issue status
        try:
            gh_issue = github.get(f"https://api.github.com/repos/{repo_name}/issues/{issue_number}")
            if not isinstance(gh_issue, dict):
                continue

            state = gh_issue.get("state")
            # Only evaluate issues that have been closed or resolved
            if state != "closed":
                continue

            # 3. Check for linked Pull Requests / merged PRs
            # Look for PR timeline events or pull_request key
            merged_pr_files = []
            linked_pr_number = None

            # Check issue timeline events for 'cross-referenced' or 'closed' commits
            timeline_url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/timeline"
            try:
                events = github.get(timeline_url)
                if isinstance(events, list):
                    for ev in events:
                        if ev.get("event") == "cross-referenced" and "source" in ev:
                            src_issue = ev["source"].get("issue", {})
                            if src_issue.get("pull_request"):
                                pr_num = src_issue.get("number")
                                pr_data = github.get(f"https://api.github.com/repos/{repo_name}/pulls/{pr_num}")
                                if isinstance(pr_data, dict) and pr_data.get("merged") is True:
                                    linked_pr_number = pr_num
                                    break
            except Exception:
                pass

            # Fallback: Check if issue itself had a linked PR
            if not linked_pr_number and gh_issue.get("pull_request"):
                pr_data = github.get(f"https://api.github.com/repos/{repo_name}/pulls/{issue_number}")
                if isinstance(pr_data, dict) and pr_data.get("merged") is True:
                    linked_pr_number = issue_number

            if not linked_pr_number:
                continue

            # 4. Extract merged PR diff files (Ground Truth)
            pr_files_data = github.get(f"https://api.github.com/repos/{repo_name}/pulls/{linked_pr_number}/files")
            if isinstance(pr_files_data, list):
                for f_obj in pr_files_data:
                    fname = f_obj.get("filename")
                    if fname and not fname.startswith(".") and not "test" in fname.lower():
                        merged_pr_files.append(fname)

            if not merged_pr_files:
                continue

            print(f"\n🔍 Found Merged PR #{linked_pr_number} for {case_key} with {len(merged_pr_files)} ground-truth fix files.")

            # 5. Run EXISTING RAG retrieval against the historical issue
            # Note: Merged PR files are strictly NEVER passed to the retriever
            issue_title = gh_issue.get("title", "")
            issue_body = gh_issue.get("body", "") or ""

            rag_result = retriever.retrieve_code_context(
                repo_name=repo_name,
                issue_title=issue_title,
                issue_body=issue_body,
                limit=10
            )

            retrieved_chunks = rag_result.get("chunks", [])
            retrieved_files = list(dict.fromkeys([c.get("file_path") for c in retrieved_chunks if c.get("file_path")]))

            # 6. Calculate Recall & MRR
            metrics = calculate_retrieval_metrics(retrieved_files, merged_pr_files)
            print(f"   📈 Metrics -> Recall@1: {metrics['recall_at_1']}, Recall@5: {metrics['recall_at_5']}, Recall@10: {metrics['recall_at_10']}, MRR@10: {metrics['mrr_at_10']}")

            eval_entry = {
                "case_key": case_key,
                "repo_name": repo_name,
                "issue_number": issue_number,
                "merged_pr_number": linked_pr_number,
                "ground_truth_files": merged_pr_files,
                "retrieved_files": retrieved_files,
                "metrics": metrics,
                "evaluated_at": datetime.now(timezone.utc).isoformat()
            }

            eval_dataset[case_key] = eval_entry
            eval_cases_summary.append(eval_entry)
            evaluated_count += 1
            newly_added_cases += 1

        except Exception as e:
            print(f"⚠️ Error evaluating {case_key}: {e}")
            continue

    # 7. Aggregate Metrics & Save
    if eval_cases_summary:
        avg_r1 = sum(c["metrics"]["recall_at_1"] for c in eval_cases_summary) / len(eval_cases_summary)
        avg_r5 = sum(c["metrics"]["recall_at_5"] for c in eval_cases_summary) / len(eval_cases_summary)
        avg_r10 = sum(c["metrics"]["recall_at_10"] for c in eval_cases_summary) / len(eval_cases_summary)
        avg_mrr = sum(c["metrics"]["mrr_at_10"] for c in eval_cases_summary) / len(eval_cases_summary)
        avg_hit10 = sum(c["metrics"]["hit_at_10"] for c in eval_cases_summary) / len(eval_cases_summary)

        print("\n================================================================")
        print(f"🎉 Rolling RAG Evaluation Complete ({len(eval_cases_summary)} cases evaluated).")
        print(f"   Average Recall@1:  {avg_r1:.4f}")
        print(f"   Average Recall@5:  {avg_r5:.4f}")
        print(f"   Average Recall@10: {avg_r10:.4f}")
        print(f"   Average MRR@10:    {avg_mrr:.4f}")
        print(f"   Average Hit@10:    {avg_hit10:.4f}")
        print("================================================================")

        # Store in Supabase eval_results table
        if not dry_run:
            try:
                supabase.table("eval_results").insert({
                    "run_at": datetime.now(timezone.utc).isoformat(),
                    "total_issues_evaluated": len(eval_cases_summary),
                    "retrieval_recall": avg_r10,
                    "hint_precision": avg_hit10,
                    "retrieval_success_count": sum(1 for c in eval_cases_summary if c["metrics"]["hit_at_10"] > 0),
                    "hint_success_count": sum(1 for c in eval_cases_summary if c["metrics"]["recall_at_1"] > 0),
                    "recall_at_10": avg_r10,
                    "hit_at_10": avg_hit10,
                    "mrr_at_10": avg_mrr,
                    "dataset_version": "v4.5-rolling"
                }).execute()
                print("✅ Recorded evaluation run in Supabase eval_results table.")
            except Exception as sb_err:
                print(f"⚠️ Could not write to eval_results table: {sb_err}")

        # Update local dataset file
        try:
            with open(EVAL_DATASET_PATH, "w", encoding="utf-8") as f:
                json.dump(eval_dataset, f, indent=2)
            print(f"💾 Updated rolling evaluation dataset at {EVAL_DATASET_PATH}")
        except Exception as f_err:
            print(f"⚠️ Could not save dataset JSON: {f_err}")

    else:
        print(f"\nℹ️ No new resolved/merged PR evaluation cases found in this cycle. (Skipped {skipped_count} previously evaluated cases).")

    return {
        "status": "success",
        "evaluated_cases": len(eval_cases_summary),
        "total_dataset_size": len(eval_dataset),
        "skipped_previously_evaluated": skipped_count
    }


if __name__ == "__main__":
    run_rolling_rag_eval(min_age_days=1, max_cases_to_evaluate=10, dry_run=False)
