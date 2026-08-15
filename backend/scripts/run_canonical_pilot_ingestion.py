"""
GitNova v4.4.1 — Canonical Pilot Ingestion Script

Runs the single canonical pipeline gateway over 10-15 authentic, verified, open GitHub issues
spanning Python, TypeScript, JavaScript, Rust, and Go.
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from supabase import create_client
from app.pipeline.github_client import GitHubClient
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline

PILOT_TARGETS = [
    # Pallets Click (Python)
    ("pallets/click", 3740),
    ("pallets/click", 3696),
    ("pallets/click", 3652),
    ("pallets/click", 3571),
    # PSF Requests (Python)
    ("psf/requests", 7599),
    ("psf/requests", 7574),
    ("psf/requests", 7564),
    ("psf/requests", 7547),
    # Facebook Docusaurus (TypeScript)
    ("facebook/docusaurus", 12358),
    # Express (JavaScript)
    ("expressjs/express", 7391),
    # Sharkdp Bat (Rust)
    ("sharkdp/bat", 3887),
    ("sharkdp/bat", 3878),
    # SPF13 Cobra (Go)
    ("spf13/cobra", 2481),
    ("spf13/cobra", 2477),
    ("spf13/cobra", 2475)
]

def run_pilot_ingestion():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials missing.")
        return

    supabase = create_client(supabase_url, supabase_key)
    github = GitHubClient(supabase_client=supabase)

    print("==========================================================================")
    print("RUNNING CANONICAL INGESTION PILOT ON AUTHENTIC OPEN GITHUB ISSUES")
    print("==========================================================================\n")

    results = []

    for idx, (repo_name, issue_num) in enumerate(PILOT_TARGETS, 1):
        print(f"[{idx}/{len(PILOT_TARGETS)}] Ingesting {repo_name} #{issue_num} through Canonical Gateway...")
        try:
            res = CanonicalIngestionPipeline.ingest_and_process_issue(
                repo_full_name=repo_name,
                github_issue_number=issue_num,
                supabase_client=supabase,
                github_client=github,
                dry_run=False
            )
            results.append(res)
            print(f"      Result: published={res.get('published')}, tier={res.get('difficulty_tier')}, score={res.get('suitability_score')}, status={res.get('availability_status')}")
            if not res.get("published"):
                print(f"      Reason: {res.get('reason')}")
        except Exception as e:
            print(f"      ❌ Exception during canonical ingestion: {e}")
            results.append({
                "success": False,
                "published": False,
                "repo_full_name": repo_name,
                "github_issue_number": issue_num,
                "reason": str(e)
            })
        print()

    out_path = "research/canonical_pilot_ingestion_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    published_count = sum(1 for r in results if r.get("published"))
    print("==========================================================================")
    print(f"PILOT INGESTION COMPLETE: {published_count}/{len(PILOT_TARGETS)} issues verified & published.")
    print(f"Results written to {out_path}.")
    print("==========================================================================")

if __name__ == "__main__":
    run_pilot_ingestion()
