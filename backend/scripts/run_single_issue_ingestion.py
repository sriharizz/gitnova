"""
GitNova Single Issue Ingestion Runner

Executes strictly ONE canonical issue through the entire hardened pipeline:
- IngestionLock mutual exclusion guard
- Gemini 3.6 Flash structured LLM generation
- Commit-SHA snapshot idempotency check
- AST code retrieval + Grounding Verification
- 10-Stage Contribution Journey generation
- Supabase atomic persistence
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

from app.core.lock import IngestionLock
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline


def run_single_test_ingestion(repo_name: str, issue_number: int):
    print("=" * 75)
    print(f"CANONICAL INGESTION VERIFICATION: {repo_name} #{issue_number}")
    print("=" * 75)

    with IngestionLock():
        print("🔒 IngestionLock successfully acquired.")
        t0 = time.time()
        res = CanonicalIngestionPipeline.ingest_and_process_issue(repo_name, issue_number)
        dt = time.time() - t0

    print(f"\nPipeline finished in {dt:.2f}s.")
    print("=" * 75)
    print(f"SUCCESS:         {res.get('success')}")
    print(f"PUBLISHED:       {res.get('published')}")
    print(f"REPO:            {res.get('repo_full_name')} #{res.get('github_issue_number')}")
    print(f"TITLE:           {res.get('title')}")
    print(f"DIFFICULTY:      {res.get('difficulty_tier')}")
    print(f"VERIFICATION:    {res.get('verification_status')} (Reasons: {res.get('verification_reasons')})")
    print(f"AVAILABILITY:    {res.get('availability_status')}")

    exp = res.get("explanation", {})
    if exp:
        print("\n--- LLM GROUNDED EXPLANATION (Gemini 3.6 Flash) ---")
        print(f"Summary:         {exp.get('summary')}")
        print(f"Relevant Files:  {len(exp.get('relevant_locations', []))} verified citations")
        for loc in exp.get("relevant_locations", []):
            print(f"   • {loc.get('file_path')} (lines {loc.get('line_start')}-{loc.get('line_end')})")
        print(f"Prereq Concepts: {len(exp.get('prerequisite_concepts', []))} concepts")
        print(f"Step Plan:       {len(exp.get('step_by_step_plan', []))} steps")

    journey = res.get("contribution_journey", {})
    if journey:
        stages = journey.get("stages", [])
        print(f"\n--- DETERMINISTIC CONTRIBUTION JOURNEY ---")
        print(f"Total Stages:    {len(stages)} / 10 generated")
        for idx, st in enumerate(stages, 1):
            print(f"  Stage {idx:02d}: {st.get('stage_name')} ({len(st.get('actionable_tasks', []))} tasks)")

    print("=" * 75)
    return res


if __name__ == "__main__":
    target_repo = sys.argv[1] if len(sys.argv) > 1 else "psf/requests"
    target_issue = int(sys.argv[2]) if len(sys.argv) > 2 else 7599
    run_single_test_ingestion(target_repo, target_issue)
