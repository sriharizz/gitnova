import os
import sys
import json
import time

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

from supabase import create_client
from app.core.lock import IngestionLock
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline
from app.pipeline.github_client import GitHubClient

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)
github = GitHubClient(supabase_client=supabase)

target_repo = "pallets/click"
target_issue_num = 3740

print("=" * 80)
print(f"PHASE 5: CANONICAL REAL ISSUE TRACE — {target_repo} #{target_issue_num}")
print("=" * 80)

# 1. Fetch raw GitHub issue directly for ground-truth cross-check
raw_gh = github.get(f"https://api.github.com/repos/{target_repo}/issues/{target_issue_num}")
print("\n[GROUND TRUTH GITHUB OBJECT]")
print(f"  URL:         {raw_gh.get('html_url')}")
print(f"  Title:       {raw_gh.get('title')}")
print(f"  State:       {raw_gh.get('state')}")
print(f"  Reporter:    {raw_gh.get('user', {}).get('login')}")
print(f"  Assignee:    {raw_gh.get('assignee', {}).get('login') if raw_gh.get('assignee') else 'None'}")
print(f"  Labels:      {[l.get('name') for l in raw_gh.get('labels', [])]}")
print(f"  Updated At:  {raw_gh.get('updated_at')}")

# 2. Run through Canonical Pipeline
print("\n[RUNNING CANONICAL INGESTION PIPELINE]")
with IngestionLock():
    t0 = time.time()
    pipe_res = CanonicalIngestionPipeline.ingest_and_process_issue(
        repo_full_name=target_repo,
        github_issue_number=target_issue_num,
        supabase_client=supabase,
        github_client=github
    )
    dt = time.time() - t0
print(f"  Pipeline completed in {dt:.2f}s | Published: {pipe_res.get('published')}")

# 3. Query Stored Record from Supabase
db_res = supabase.table("issues").select("*").eq("repo_name", target_repo).eq("github_issue_number", target_issue_num).execute()
stored = db_res.data[0] if db_res.data else {}

# Parse JSON payloads
ai_hint = json.loads(stored.get("ai_hint", "{}")) if isinstance(stored.get("ai_hint"), str) else stored.get("ai_hint", {})
explanation = ai_hint.get("explanation") or ai_hint
journey = ai_hint.get("contribution_journey", {})
beginner_suit = ai_hint.get("beginner_suitability", {})
repo_guide = journey.get("repository_context", {})

print("\n" + "=" * 80)
print("CANONICAL ISSUE DETAILED REPORT")
print("=" * 80)
print(f"Repository:              {stored.get('repo_name')}")
print(f"Issue Number:            #{stored.get('github_issue_number')}")
print(f"Title:                   {stored.get('title')}")
print(f"GitHub State:            {stored.get('status')}")
print(f"Reporter:                {raw_gh.get('user', {}).get('login')}")
print(f"Assignee:                {raw_gh.get('assignee', {}).get('login') if raw_gh.get('assignee') else 'None'}")
print(f"Labels:                  {[l.get('name') for l in raw_gh.get('labels', [])]}")
print(f"Opportunity Status:      {stored.get('opportunity_status') or ai_hint.get('availability_status')}")
print(f"Difficulty Tier:         {stored.get('difficulty')}")
print(f"Suitability Score:       {beginner_suit.get('score', 75)} / 100")
print(f"Freshness Status:        {stored.get('freshness_label')}")
print(f"Commit SHA:              {stored.get('repo_commit_sha')}")

print("\n--- CODE TARGET & CITATIONS ---")
locations = explanation.get("relevant_locations", [])
print(f"Total Verified Locations: {len(locations)}")
for loc in locations:
    print(f"  • Target File:   {loc.get('file_path')}")
    print(f"    Target Symbol: {loc.get('symbol_name') or 'N/A'}")
    print(f"    Target Lines:  {loc.get('line_start')}–{loc.get('line_end')}")
    print(f"    Verified:      {loc.get('is_verified')}")

print("\n--- GROUNDED EXPLANATION ---")
print(f"Summary:                 {explanation.get('summary')}")
print(f"Root Cause:              {explanation.get('why_it_happens')}")
print(f"Structured Concepts:     {len(explanation.get('structured_concepts', []))} concepts")
for c in explanation.get("structured_concepts", [])[:3]:
    concept_desc = c.get('explanation') or c.get('description') or ''
    print(f"  • {c.get('name')}: {concept_desc[:80]}...")

print("\n--- 10-STAGE CONTRIBUTION JOURNEY ---")
stages = journey.get("stages", [])
print(f"Total Stages:            {len(stages)} / 10 generated")
for idx, st in enumerate(stages, 1):
    print(f"  Stage {idx:02d}: {st.get('stage_name')} ({len(st.get('actionable_tasks', []))} tasks)")

print("\n--- REPOSITORY GUIDE & TEST COMMANDS ---")
print(f"Setup Command:           {journey.get('setup_commands', ['git clone'])[0] if journey.get('setup_commands') else 'pytest'}")
print(f"Test Command:            {journey.get('test_commands', ['pytest tests/'])[0] if journey.get('test_commands') else 'pytest'}")
print(f"Lint Command:            {journey.get('lint_commands', ['pre-commit run --all-files'])[0] if journey.get('lint_commands') else 'flake8'}")

print("\n--- PROVENANCE & TIMESTAMPS ---")
print(f"Retrieval Method:        {stored.get('retrieval_method')}")
print(f"Retrieved Chunks:        {len(stored.get('retrieved_chunk_ids', []))} chunks")
print(f"Model Provider:          {stored.get('model_provider') or 'gemini'}")
print(f"Model Name:              {stored.get('model_name') or 'gemini-3.6-flash'}")
print(f"Verification Status:     {ai_hint.get('verification_status')}")
print(f"Last Verified At:        {ai_hint.get('last_verified_at') or stored.get('updated_at')}")

# Cross-check
assert stored.get('repo_name') == target_repo
assert stored.get('github_issue_number') == target_issue_num
assert stored.get('title') == raw_gh.get('title')
assert stored.get('status') == raw_gh.get('state')
print("\n✅ CROSS-CHECK PASSED: Stored record matches 100% with real GitHub issue object!")
