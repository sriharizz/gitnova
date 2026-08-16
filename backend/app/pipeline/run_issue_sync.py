"""
GitNova v4.2 — 12-Hour Incremental Issue Synchronization & Janitor Worker

Executes the automated 12-hour background sync pipeline:
  1. Fetch active repos from Supabase.
  2. Fetch new/updated issues via GitHub API (using ETags & since filter).
  3. Pre-filter rants/epics/vague tasks (pure Python, zero cost).
  4. Ensure repo code is indexed (Commit-SHA Gated).
  5. Run Sprint 7 hybrid RRF code retrieval.
  6. Compute deterministic issue difficulty score & tier.
  7. Generate grounded LLM IssueExplanation.
  8. Run GroundingVerifier to assign verification_status (VERIFIED | NEEDS_REVIEW | INVALID).
  9. Upsert precomputed issue record to Supabase.
 10. Run Janitor soft-delete routine (mark closed issues is_published=FALSE).
 11. Log run audit telemetry to pipeline_runs table.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from dotenv import load_dotenv
from supabase import create_client


from app.core.config import settings
from app.pipeline.github_client import GitHubClient
from app.pipeline.data_integrity_firewall import DataIntegrityFirewall
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator
from app.clients.llm.gemini import GeminiQuotaTracker


def run_12h_incremental_sync(dry_run: bool = False, target_repo: str = None, max_repos: int = 40) -> dict:
    """
    Main 12-hour pipeline execution function.
    Can be run as a standalone script or called by GitHub Actions worker.
    """
    start_time = time.time()
    supabase_url = getattr(settings, "supabase_url", "") or os.getenv("SUPABASE_URL", "")
    supabase_key = getattr(settings, "supabase_key", "") or os.getenv("SUPABASE_KEY", "")

    if not supabase_url or not supabase_key:
        print("❌ CRITICAL: SUPABASE_URL or SUPABASE_KEY missing.")
        return {"status": "failed", "error": "Missing Supabase credentials"}

    supabase = create_client(supabase_url, supabase_key)
    github = GitHubClient(supabase_client=supabase)

    # 1. Start pipeline audit log
    run_id = None
    if not dry_run:
        try:
            run_resp = supabase.table("pipeline_runs").insert({
                "run_type": "issue_scan",
                "triggered_by": "github_actions_12h",
                "status": "running",
                "started_at": datetime.now().isoformat()
            }).execute()
            if run_resp.data:
                run_id = run_resp.data[0]["id"]
        except Exception as err:
            print(f"⚠️ Failed to create pipeline_runs audit record: {err}")

    items_found = 0
    items_published = 0
    repos_processed = 0
    errors = []

    try:
        # 2. Fetch active qualified repositories with Language-Balanced Round-Robin Distribution
        if target_repo:
            repos_resp = supabase.table("repos").select("*").eq("full_name", target_repo).execute()
            active_repos = repos_resp.data or []
        else:
            repos_resp = supabase.table("repos").select("*").eq("is_active", True).order("score", desc=True).limit(100).execute()
            all_active = repos_resp.data or []

            # Group by language to balance across TypeScript, Python, JS, Go, Rust, Java, Dart, etc.
            from collections import defaultdict
            lang_buckets = defaultdict(list)
            for r in all_active:
                lang = r.get("language") or "Other"
                lang_buckets[lang].append(r)

            # Round-robin interleave across languages
            active_repos = []
            max_depth = max((len(v) for v in lang_buckets.values()), default=0)
            for depth in range(max_depth):
                for lang, bucket in lang_buckets.items():
                    if depth < len(bucket):
                        active_repos.append(bucket[depth])
                        if len(active_repos) >= max_repos:
                            break
                if len(active_repos) >= max_repos:
                    break

        print(f"🚀 Starting 12-hour sync across {len(active_repos)} language-balanced active repositories...")

        since_time = (datetime.utcnow() - timedelta(hours=12)).isoformat() + "Z"

        quota_tracker = GeminiQuotaTracker()

        for repo in active_repos:
            if quota_tracker.is_daily_quota_exhausted():
                print(f"🛑 [QuotaBudget] Daily Gemini limit reached ({quota_tracker.rpd_limit} RPD). Gracefully stopping 12-hour sync.")
                break

            repo_id = repo["id"]
            repo_name = repo["full_name"]
            repos_processed += 1
            print(f"\n📦 Processing {repo_name}...")

            # Fetch open issues updated in the last 12 hours
            try:
                issues_url = f"https://api.github.com/repos/{repo_name}/issues"
                raw_issues = github.get(issues_url, params={"state": "open", "since": since_time, "per_page": 10})
                if not isinstance(raw_issues, list):
                    raw_issues = []
            except Exception as gh_err:
                print(f"⚠️ GitHub API error for {repo_name}: {gh_err}")
                errors.append(f"{repo_name}: {gh_err}")
                continue

            items_found += len(raw_issues)
            print(f"   Found {len(raw_issues)} candidate issues.")

            for raw_issue in raw_issues:
                if quota_tracker.is_daily_quota_exhausted():
                    print(f"🛑 [QuotaBudget] Daily Gemini limit reached. Deferring remaining issues to next scheduled run.")
                    break

                # Step 1: Pre-filter out Pull Requests immediately
                if "pull_request" in raw_issue or "/pull/" in raw_issue.get("html_url", ""):
                    continue

                issue_num = raw_issue["number"]
                print(f"   📌 Processing canonical candidate #{issue_num}: '{raw_issue.get('title', '')[:40]}...'")

                # Ingest through Single Canonical Pipeline Gateway
                res = CanonicalIngestionPipeline.ingest_and_process_issue(
                    repo_full_name=repo_name,
                    github_issue_number=issue_num,
                    supabase_client=supabase,
                    github_client=github,
                    dry_run=dry_run
                )

                if res.get("published"):
                    items_published += 1
                    print(f"      ✅ Verified & Published Issue #{issue_num} ({res.get('difficulty_tier')})")
                else:
                    print(f"      ⏩ Skipped publication: {res.get('reason') or 'Failed quality/eligibility gate'}")

        # 9. Extended Janitor Routine: Continuous Published Feed Protection
        print("\n🧹 Running Extended Janitor Audit on Published Issues...")
        janitor_unpublished_count = 0
        if not dry_run:
            pub_issues_resp = supabase.table("issues").select("id, repo_id, github_issue_number, repos!inner(full_name)").eq("is_published", True).execute()
            for pub_iss in (pub_issues_resp.data or []):
                r_name = pub_iss.get("repos", {}).get("full_name")
                i_num = pub_iss["github_issue_number"]
                if not r_name:
                    continue
                try:
                    check_url = f"https://api.github.com/repos/{r_name}/issues/{i_num}"
                    g_issue = github.get(check_url)
                    
                    # Verify canonical identity and open state
                    fw_check = DataIntegrityFirewall.verify_canonical_identity(
                        repo_full_name=r_name,
                        github_issue_number=i_num,
                        raw_gh_data=g_issue
                    )

                    should_unpublish = False
                    unpublish_reason = None

                    if fw_check["data_integrity_status"] != "VERIFIED":
                        should_unpublish = True
                        unpublish_reason = fw_check.get("rejection_reason")
                    elif fw_check["canonical_state"] != "open":
                        should_unpublish = True
                        unpublish_reason = "Issue was closed on GitHub."
                    elif fw_check["assignees"]:
                        should_unpublish = True
                        unpublish_reason = f"Issue is now assigned to @{fw_check['assignees'][0]}."

                    if should_unpublish:
                        supabase.table("issues").update({
                            "github_state": fw_check.get("canonical_state", "closed"),
                            "is_published": False,
                            "closed_at": datetime.now().isoformat() if fw_check.get("canonical_state") == "closed" else None
                        }).eq("id", pub_iss["id"]).execute()
                        janitor_unpublished_count += 1
                        print(f"   🔒 Janitor unpublished #{i_num} ({r_name}): {unpublish_reason}")
                except Exception as j_err:
                    pass

        duration = int(time.time() - start_time)
        print(f"\n🎉 12-Hour Sync Completed in {duration}s. Repos: {repos_processed}, Found: {items_found}, Published: {items_published}, Unpublished: {janitor_unpublished_count}")

        # 10. Finalize audit run log
        if run_id and not dry_run:
            supabase.table("pipeline_runs").update({
                "finished_at": datetime.now().isoformat(),
                "repos_processed": repos_processed,
                "items_found": items_found,
                "items_published": items_published,
                "status": "success",
                "metadata": {"janitor_closed": janitor_closed_count, "errors": errors}
            }).eq("id", run_id).execute()

        return {
            "status": "success",
            "repos_processed": repos_processed,
            "items_found": items_found,
            "items_published": items_published,
            "janitor_closed": janitor_closed_count,
            "duration_seconds": duration
        }

    except Exception as fatal_err:
        print(f"❌ Fatal Pipeline Error: {fatal_err}")
        if run_id and not dry_run:
            try:
                supabase.table("pipeline_runs").update({
                    "finished_at": datetime.now().isoformat(),
                    "status": "failed",
                    "error_log": str(fatal_err)
                }).eq("id", run_id).execute()
            except Exception:
                pass
        return {"status": "failed", "error": str(fatal_err)}


if __name__ == "__main__":
    load_dotenv()
    import argparse
    parser = argparse.ArgumentParser(description="GitNova 12-Hour Issue Sync & Janitor Worker")
    parser.add_argument("--dry-run", action="store_true", help="Run without persisting to Supabase")
    parser.add_argument("--repo", type=str, default=None, help="Target specific repository (e.g. facebook/docusaurus)")
    parser.add_argument("--max-repos", type=int, default=40, help="Maximum repositories to process in this run")
    args = parser.parse_args()

    run_12h_incremental_sync(dry_run=args.dry_run, target_repo=args.repo, max_repos=args.max_repos)
