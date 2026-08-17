"""
GitNova v4.5 — 12-Hour Incremental Issue Synchronization & Janitor Worker

Executes the automated 12-hour background sync pipeline with:
  1. Deterministic Language-Balanced Repository Rotation (zero repo starvation).
  2. Safe Bounded Issue Pagination (up to configured max candidates).
  3. Zero-cost unchanged issue caching (no redundant Gemini calls).
  4. Commit-SHA gated AST code retrieval.
  5. Deterministic difficulty & 10-point fail-closed publication gating.
  6. Janitor soft-delete routine for closed/assigned issues.
  7. Persistent rotation telemetry stored in pipeline_runs.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

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
from app.pipeline.pipeline_tracer import PipelineTracer, set_current_tracer


def get_rotated_repositories(
    supabase_client: Any,
    max_repos: int = 40,
    target_repo: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int, int, int]:
    """
    Computes a deterministic, language-balanced repository slice using a persistent cursor.
    
    Algorithm:
      1. Fetch all active repositories ordered by score DESC, full_name ASC.
      2. Group repositories into language buckets (Python, TypeScript, Go, Rust, etc.).
      3. Round-robin interleave across buckets to build a deterministic Master Rotation Ring.
      4. Fetch the last rotation offset from the most recent pipeline_runs record.
      5. Slice max_repos starting from offset (wrapping around cleanly).
      6. Return (selected_repos, current_offset, next_offset, total_active).
    """
    if target_repo:
        repos_resp = supabase_client.table("repos").select("*").eq("full_name", target_repo).execute()
        target_list = repos_resp.data or []
        return (target_list, 0, 0, len(target_list))

    # Step 1: Query all active repositories
    repos_resp = (
        supabase_client.table("repos")
        .select("*")
        .eq("is_active", True)
        .order("score", desc=True)
        .order("full_name", desc=False)
        .execute()
    )
    all_active = repos_resp.data or []
    if not all_active:
        return ([], 0, 0, 0)

    total_active = len(all_active)

    # Step 2: Group by language (preserving score DESC ordering within each bucket)
    lang_buckets = defaultdict(list)
    for r in all_active:
        lang = r.get("language") or "Other"
        lang_buckets[lang].append(r)

    # Step 3: Round-robin interleave across sorted languages to build Master Rotation Ring
    master_ring = []
    max_depth = max((len(v) for v in lang_buckets.values()), default=0)
    for depth in range(max_depth):
        for lang in sorted(lang_buckets.keys()):
            bucket = lang_buckets[lang]
            if depth < len(bucket):
                master_ring.append(bucket[depth])

    # Step 4: Retrieve persistent rotation offset from the last pipeline_runs record
    current_offset = 0
    try:
        last_run_resp = (
            supabase_client.table("pipeline_runs")
            .select("metadata")
            .eq("run_type", "issue_scan")
            .order("started_at", desc=True)
            .limit(5)
            .execute()
        )
        for run_row in (last_run_resp.data or []):
            meta = run_row.get("metadata") or {}
            if isinstance(meta, dict) and "next_rotation_offset" in meta:
                current_offset = int(meta["next_rotation_offset"]) % total_active
                break
    except Exception as e:
        print(f"⚠️ Rotation cursor lookup notice: {e}")
        current_offset = 0

    # Step 5: Slice max_repos starting from current_offset with modulo wrap-around
    effective_max = min(max_repos, total_active)
    selected_repos = []
    for i in range(effective_max):
        idx = (current_offset + i) % total_active
        selected_repos.append(master_ring[idx])

    next_offset = (current_offset + effective_max) % total_active
    return (selected_repos, current_offset, next_offset, total_active)


def run_12h_incremental_sync(
    dry_run: bool = False,
    target_repo: Optional[str] = None,
    max_repos: int = 40,
    max_candidates_per_repo: int = 15,
    max_pages_per_repo: int = 3,
    lookback_hours: int = 12
) -> dict:
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

    # 1. Fetch active qualified repositories using Deterministic Rotation
    active_repos, current_offset, next_offset, total_active = get_rotated_repositories(
        supabase_client=supabase,
        max_repos=max_repos,
        target_repo=target_repo
    )

    print(f"🚀 Starting 12-hour sync across {len(active_repos)}/{total_active} rotated active repositories (Offset: {current_offset} -> Next: {next_offset})...")

    # 2. Start pipeline audit log
    run_id = None
    if not dry_run:
        try:
            run_resp = supabase.table("pipeline_runs").insert({
                "run_type": "issue_scan",
                "triggered_by": "github_actions_12h",
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "rotation_offset": current_offset,
                    "next_rotation_offset": next_offset,
                    "total_active_repos": total_active,
                    "max_repos_limit": max_repos,
                    "max_candidates_per_repo": max_candidates_per_repo
                }
            }).execute()
            if run_resp.data:
                run_id = run_resp.data[0]["id"]
        except Exception as err:
            print(f"⚠️ Failed to create pipeline_runs audit record: {err}")

    # Initialize Diagnostic Pipeline Tracer
    selected_repo_metadata = [
        {
            "full_name": r.get("full_name"),
            "id": r.get("id"),
            "language": r.get("language"),
            "score": r.get("score"),
            "selection_rank": i + 1,
            "rotation_position": (current_offset + i) % max(1, total_active),
            "is_active": r.get("is_active")
        }
        for i, r in enumerate(active_repos)
    ]

    tracer_run_id = f"run_{run_id[:8]}" if run_id else None
    tracer = PipelineTracer(
        run_id=tracer_run_id,
        metadata={
            "dry_run": dry_run,
            "max_repos": max_repos,
            "max_candidates_per_repo": max_candidates_per_repo,
            "rotation_offset": current_offset,
            "next_rotation_offset": next_offset,
            "lookback_hours": lookback_hours,
            "selected_repositories": selected_repo_metadata
        }
    )
    set_current_tracer(tracer)

    items_found = 0
    items_published = 0
    repos_processed = 0
    errors = []

    try:
        since_time = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat().replace("+00:00", "Z")
        quota_tracker = GeminiQuotaTracker()

        for repo in active_repos:
            if quota_tracker.is_daily_quota_exhausted():
                print(f"🛑 [QuotaBudget] Daily Gemini limit reached ({quota_tracker.rpd_limit} RPD). Gracefully stopping 12-hour sync.")
                break

            repo_name = repo["full_name"]
            repos_processed += 1
            print(f"\n📦 Processing [{repos_processed}/{len(active_repos)}] {repo_name}...")

            # Fetch open issues with safe bounded pagination
            try:
                raw_issues = github.get_issues_paginated(
                    repo_full_name=repo_name,
                    state="open",
                    since=since_time,
                    max_candidates=max_candidates_per_repo,
                    max_pages=max_pages_per_repo,
                    per_page=min(max_candidates_per_repo, 15)
                )
            except Exception as gh_err:
                print(f"⚠️ GitHub API error for {repo_name}: {gh_err}")
                errors.append(f"{repo_name}: {gh_err}")
                continue

            items_found += len(raw_issues)
            print(f"   Found {len(raw_issues)} candidate issues (paginated).")

            for raw_issue in raw_issues:
                # Stage 1: Trace EVERY raw discovered issue immediately
                trace_id = tracer.record_stage_1_discovery(
                    repo_full_name=repo_name,
                    raw_issue=raw_issue,
                    repo_id=repo.get("id"),
                    page_number=1,
                    discovery_source="github_api_paginated",
                    language=repo.get("language")
                )

                if quota_tracker.is_daily_quota_exhausted():
                    print(f"🛑 [QuotaBudget] Daily Gemini limit reached. Deferring remaining issues to next scheduled run.")
                    tracer.record_stage_2_prefilter(
                        trace_id,
                        passed=False,
                        rule_id="QUOTA_EXHAUSTED",
                        reason="Daily Gemini quota exhausted"
                    )
                    break

                # Pre-filter out Pull Requests immediately
                if "pull_request" in raw_issue or "/pull/" in raw_issue.get("html_url", ""):
                    tracer.record_stage_2_prefilter(
                        trace_id,
                        passed=False,
                        rule_id="PULL_REQUEST",
                        reason="Item is a pull request, not an issue"
                    )
                    continue

                issue_num = raw_issue["number"]
                print(f"   📌 Processing canonical candidate #{issue_num}: '{raw_issue.get('title', '')[:40]}...'")

                # Ingest through Single Canonical Pipeline Gateway (with fast-path cache hit check)
                res = CanonicalIngestionPipeline.ingest_and_process_issue(
                    repo_full_name=repo_name,
                    github_issue_number=issue_num,
                    supabase_client=supabase,
                    github_client=github,
                    dry_run=dry_run,
                    tracer=tracer,
                    trace_id=trace_id
                )

                if res.get("published"):
                    items_published += 1
                    print(f"      ✅ Verified & Published Issue #{issue_num} ({res.get('difficulty_tier')})")
                else:
                    print(f"      ⏩ Skipped publication: {res.get('reason') or 'Failed quality/eligibility gate'}")


        # Extended Janitor Routine: Continuous Published Feed Protection
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
                            "closed_at": datetime.now(timezone.utc).isoformat() if fw_check.get("canonical_state") == "closed" else None
                        }).eq("id", pub_iss["id"]).execute()
                        janitor_unpublished_count += 1
                        print(f"   🔒 Janitor unpublished #{i_num} ({r_name}): {unpublish_reason}")
                except Exception as j_err:
                    pass

        # Finalize Diagnostic Pipeline Trace
        tracer_summary = tracer.finish_run()
        print(f"📊 Diagnostic Pipeline Trace written to: {tracer.run_dir}")

        duration = int(time.time() - start_time)
        print(f"\n🎉 12-Hour Sync Completed in {duration}s. Repos: {repos_processed}, Found: {items_found}, Published: {items_published}, Unpublished: {janitor_unpublished_count}")

        # Finalize audit run log
        if run_id and not dry_run:
            supabase.table("pipeline_runs").update({
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "repos_processed": repos_processed,
                "items_found": items_found,
                "items_published": items_published,
                "status": "success",
                "metadata": {
                    "rotation_offset": current_offset,
                    "next_rotation_offset": next_offset,
                    "total_active_repos": total_active,
                    "janitor_unpublished": janitor_unpublished_count,
                    "trace_run_id": tracer.run_id,
                    "errors": errors
                }
            }).eq("id", run_id).execute()

        return {
            "status": "success",
            "repos_processed": repos_processed,
            "items_found": items_found,
            "items_published": items_published,
            "janitor_unpublished": janitor_unpublished_count,
            "current_offset": current_offset,
            "next_rotation_offset": next_offset,
            "total_active_repos": total_active,
            "duration_seconds": duration,
            "trace_summary": tracer_summary
        }

    except Exception as fatal_err:
        print(f"❌ Fatal Pipeline Error: {fatal_err}")
        try:
            tracer.finish_run()
        except Exception:
            pass
        if run_id and not dry_run:
            try:
                supabase.table("pipeline_runs").update({
                    "finished_at": datetime.now(timezone.utc).isoformat(),
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
    parser.add_argument("--max-candidates", type=int, default=15, help="Maximum candidates per repository")
    args = parser.parse_args()

    run_12h_incremental_sync(
        dry_run=args.dry_run,
        target_repo=args.repo,
        max_repos=args.max_repos,
        max_candidates_per_repo=args.max_candidates
    )
