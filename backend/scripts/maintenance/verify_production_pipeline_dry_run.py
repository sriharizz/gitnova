"""
GitNova — Production Pipeline Dry-Run Verification
Tests single-issue ingestion flow:
  GitHub API -> Pre-Filter -> Availability & Opportunity -> Code Retrieval -> Grounding -> Journey -> Publication Gate
in controlled dry-run mode (MAX_ISSUES=1, dry_run=True).
"""

import sys
import os
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.core.config import settings
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline

def test_dry_run():
    print("🚀 Starting Production Pipeline Controlled Dry-Run (MAX_ISSUES=1)...")
    
    # Test on a verified real target (pallets/click #3652)
    repo = "pallets/click"
    issue_num = 3652

    result = CanonicalIngestionPipeline.ingest_and_process_issue(
        repo_full_name=repo,
        github_issue_number=issue_num,
        dry_run=True
    )

    print("\n📊 Dry Run Result Summary:")
    print(f"  Success: {result.get('success')}")
    print(f"  Published: {result.get('published')}")
    print(f"  Difficulty Tier: {result.get('difficulty_tier')}")
    print(f"  Quality Score: {result.get('quality_score')}")
    print(f"  Verification Status: {result.get('verification_status')}")
    print(f"  Retrieved Chunks Count: {len(result.get('chunk_ids', []))}")
    print(f"  Target File: {result.get('target_file')}")
    print(f"  Test Command: {result.get('test_command')}")

    assert result.get("success") is True, f"Pipeline failed: {result.get('reason')}"
    print("\n✅ Controlled Dry-Run Succeeded with Zero Errors!")

if __name__ == "__main__":
    test_dry_run()
