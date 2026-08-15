import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
client = create_client(supabase_url, supabase_key)

print("=" * 80)
print("PHASE 1 & 2: POST-MIGRATION 16 REMOTE VERIFICATION & RRF TESTS")
print("=" * 80)

# A. Check Schema & Columns
print("\n--- 1. SCHEMA & COLUMNS VERIFICATION ---")

# 1. issues columns
issues_v44_cols = [
    "github_state", "closed_at", "difficulty_score", "difficulty_tier",
    "domain_topics", "estimated_time", "verification_status",
    "verification_reasons", "explanation"
]
missing_issue_cols = []
for c in issues_v44_cols:
    try:
        client.table("issues").select(c).limit(0).execute()
    except Exception as e:
        missing_issue_cols.append((c, str(e)))

print(f"issues table v4.4 columns: {'ALL PRESENT (9/9)' if not missing_issue_cols else f'MISSING: {missing_issue_cols}'}")

# 2. repository_snapshots.is_evaluation
is_eval_present = False
try:
    client.table("repository_snapshots").select("is_evaluation").limit(0).execute()
    is_eval_present = True
    print("repository_snapshots.is_evaluation: PRESENT")
except Exception as e:
    print(f"repository_snapshots.is_evaluation: MISSING ({e})")

# 3. user_preferences table
user_pref_present = False
try:
    client.table("user_preferences").select("id, user_id, preferred_languages, preferred_domains, preferred_difficulty").limit(0).execute()
    user_pref_present = True
    print("user_preferences table: PRESENT")
except Exception as e:
    print(f"user_preferences table: MISSING ({e})")

# 4. eval_results columns
eval_v44_cols = [
    "dataset_version", "eval_model", "recall_at_10", "hit_at_10", "mrr_at_10",
    "citation_verification_rate", "hallucination_rate",
    "solution_actionability_score", "latency_p50_ms", "latency_p95_ms"
]
missing_eval_cols = []
for c in eval_v44_cols:
    try:
        client.table("eval_results").select(c).limit(0).execute()
    except Exception as e:
        missing_eval_cols.append((c, str(e)))

print(f"eval_results table v4.4 columns: {'ALL PRESENT (10/10)' if not missing_eval_cols else f'MISSING: {missing_eval_cols}'}")

# B. Check Data Safety / Row Counts
print("\n--- 2. DATA SAFETY & ROW COUNTS ---")
for t in ["repos", "issues", "code_chunks", "repository_snapshots", "etag_cache", "eval_results", "pipeline_runs"]:
    try:
        resp = client.table(t).select("*", count="exact").limit(0).execute()
        cnt = resp.count if resp.count is not None else "(unknown)"
        print(f"  Table '{t}': {cnt} total rows present.")
    except Exception as e:
        print(f"  Table '{t}': ERROR ({e})")

# Check published issues
try:
    resp_pub = client.table("issues").select("id, repo_name, github_issue_number, title, is_published").eq("is_published", True).execute()
    print(f"  Published Issues Active: {len(resp_pub.data)} rows.")
    for r in resp_pub.data[:5]:
        print(f"    - {r.get('repo_name')} #{r.get('github_issue_number')}: {r.get('title')[:50]}")
except Exception as e:
    print(f"  Published issues query error: {e}")

# Check active snapshots
try:
    resp_snap = client.table("repository_snapshots").select("repo_name, commit_sha, status").eq("status", "ACTIVE").execute()
    print(f"  Active Repository Snapshots: {len(resp_snap.data)} snapshots.")
    for s in resp_snap.data:
        print(f"    - {s.get('repo_name')} @ {s.get('commit_sha')[:7]} ({s.get('status')})")
except Exception as e:
    print(f"  Active snapshots query error: {e}")

# C. Test RRF Directly (Phase 2)
print("\n--- 3. DIRECT RRF RPC TESTS ---")

# 1. 4-param vector call (Must resolve to canonical function without PGRST203)
print("Test 1: Vector search with 4 parameters...")
try:
    resp = client.rpc("match_chunks_vector", {
        "query_embedding": [0.0] * 768,
        "target_repo": "pallets/click",
        "target_commit": "9c4dfda064115456f91f3f9b8b209d846c4f34ef",
        "match_count": 3
    }).execute()
    print(f"  ✅ SUCCESS: match_chunks_vector (4-param) returned {len(resp.data)} rows without PGRST203!")
    if resp.data:
        print(f"     Sample chunk: {resp.data[0].get('file_path')} | sim: {resp.data[0].get('similarity'):.4f}")
except Exception as e:
    print(f"  ❌ FAILED: match_chunks_vector (4-param): {e}")

# 2. 5-param vector call (with target_repo_id)
print("\nTest 2: Vector search with 5 parameters (target_repo_id=None)...")
try:
    resp = client.rpc("match_chunks_vector", {
        "query_embedding": [0.0] * 768,
        "target_repo": "pallets/click",
        "target_commit": "9c4dfda064115456f91f3f9b8b209d846c4f34ef",
        "match_count": 3,
        "target_repo_id": None
    }).execute()
    print(f"  ✅ SUCCESS: match_chunks_vector (5-param) returned {len(resp.data)} rows!")
except Exception as e:
    print(f"  ❌ FAILED: match_chunks_vector (5-param): {e}")

# 3. 4-param lexical call (Must resolve without PGRST203)
print("\nTest 3: Lexical keyword search with 4 parameters...")
try:
    resp = client.rpc("match_chunks_lexical", {
        "query_text": "pager",
        "target_repo": "pallets/click",
        "target_commit": "9c4dfda064115456f91f3f9b8b209d846c4f34ef",
        "match_count": 3
    }).execute()
    print(f"  ✅ SUCCESS: match_chunks_lexical (4-param) returned {len(resp.data)} rows without PGRST203!")
    if resp.data:
        print(f"     Sample chunk: {resp.data[0].get('file_path')} | rank: {resp.data[0].get('lexical_rank'):.4f}")
except Exception as e:
    print(f"  ❌ FAILED: match_chunks_lexical (4-param): {e}")

# 4. 5-param lexical call
print("\nTest 4: Lexical keyword search with 5 parameters (target_repo_id=None)...")
try:
    resp = client.rpc("match_chunks_lexical", {
        "query_text": "pager",
        "target_repo": "pallets/click",
        "target_commit": "9c4dfda064115456f91f3f9b8b209d846c4f34ef",
        "match_count": 3,
        "target_repo_id": None
    }).execute()
    print(f"  ✅ SUCCESS: match_chunks_lexical (5-param) returned {len(resp.data)} rows!")
except Exception as e:
    print(f"  ❌ FAILED: match_chunks_lexical (5-param): {e}")

# 5. Isolation Guard: Unbounded query without repo or repo_id must raise error
print("\nTest 5: Isolation guard check (target_repo=None and target_repo_id=None)...")
try:
    resp = client.rpc("match_chunks_vector", {
        "query_embedding": [0.0] * 768,
        "target_repo": None,
        "target_commit": None,
        "match_count": 3,
        "target_repo_id": None
    }).execute()
    print("  ❌ WARNING: Unbounded query succeeded when it should have raised an isolation exception!")
except Exception as e:
    if "Repository isolation error" in str(e):
        print(f"  ✅ SUCCESS: Isolation guard raised expected exception: {e}")
    else:
        print(f"  ℹ️ Guard raised: {e}")

print("\n" + "=" * 80)
print("POST-MIGRATION 16 VERIFICATION SCRIPT COMPLETE")
print("=" * 80)
