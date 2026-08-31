import os
import sys
import json
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

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
client = create_client(url, key)

print("=== STEP 1: AUDITING DATA MODEL ===")
all_issues = []
offset = 0
while True:
    batch = client.table("issues").select(
        "id, repo_name, github_issue_number, title, is_published, retrieved_chunk_ids, repo_commit_sha, explanation, ai_hint, created_at, closed_at, github_state"
    ).range(offset, offset + 999).execute().data or []
    if not batch:
        break
    all_issues.extend(batch)
    offset += len(batch)
    if len(batch) < 1000:
        break

print(f"Total Issues in DB: {len(all_issues)}")

with_chunk_ids = [i for i in all_issues if i.get("retrieved_chunk_ids") and len(i.get("retrieved_chunk_ids")) > 0]
print(f"Issues with non-null retrieved_chunk_ids: {len(with_chunk_ids)}")

for s in with_chunk_ids[:5]:
    rn = s.get("repo_name")
    num = s.get("github_issue_number")
    c_ids = s.get("retrieved_chunk_ids")
    sha = s.get("repo_commit_sha")
    print(f"Sample {rn}#{num}: chunk_ids count = {len(c_ids)} | sample_ids = {c_ids[:2]} | commit_sha = {sha}")

# Check code_chunks table
chunk_count_resp = client.table("code_chunks").select("chunk_id", count="exact", head=True).execute()
print(f"Total chunks in code_chunks table: {chunk_count_resp.count}")

# Test resolving sample chunk_ids to file_path
if with_chunk_ids:
    for s in with_chunk_ids[:5]:
        sample_ids = s.get("retrieved_chunk_ids") or []
        rn = s.get("repo_name")
        num = s.get("github_issue_number")
        chunk_rows = client.table("code_chunks").select("chunk_id, repo_name, file_path, symbol_name, start_line, end_line, commit_sha").in_("chunk_id", sample_ids[:10]).execute().data or []
        resolved_files = list(dict.fromkeys([cr.get("file_path") for cr in chunk_rows if cr.get("file_path")]))
        print(f"Issue {rn}#{num}: {len(sample_ids)} stored chunk IDs -> {len(chunk_rows)} resolved in code_chunks -> {len(resolved_files)} unique files: {resolved_files[:3]}")

# Also check explanation.relevant_locations in ai_hint / explanation JSON
exp_loc_count = 0
for i in all_issues:
    hint = i.get("ai_hint") or i.get("explanation")
    if isinstance(hint, str):
        try:
            h_obj = json.loads(hint)
            if h_obj.get("relevant_locations"):
                exp_loc_count += 1
        except Exception:
            pass
    elif isinstance(hint, dict) and hint.get("relevant_locations"):
        exp_loc_count += 1

print(f"Issues with parsed relevant_locations in explanation/ai_hint: {exp_loc_count}")

# Check closed issues in DB
closed_in_db = [i for i in all_issues if i.get("github_state") == "closed" or i.get("closed_at")]
print(f"Issues marked closed in DB: {len(closed_in_db)}")

# Check eval_results table
eval_results_count = client.table("eval_results").select("id", count="exact", head=True).execute().count
print(f"Total runs in eval_results table: {eval_results_count}")
