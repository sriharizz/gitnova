"""
GitNova Direct Supabase Cleaner
===============================
Fetches all issues currently in Supabase, runs them through our
newly fortified v2.1 pipeline validators, and deletes any issues
that suffer from Template Collapse, Hallucination, or Low Quality.
"""

import os
import sys
import time
from dotenv import load_dotenv
from supabase import create_client

# Add the backend directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.pipeline.pre_filter import pre_filter_issue_from_csv
from app.pipeline.post_validator import validate_llama_output
from app.pipeline.quality_scorer import compute_quality_score
from app.pipeline.repo_grounding import get_repo_context_from_name

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("❌ CRITICAL: Supabase credentials missing from .env")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def clean_database():
    print("🚀 INIT: Direct Database Cleaner (v2.1 Filters)")
    
    # 1. Fetch all issues
    print("📥 Fetching existing issues from Supabase...")
    response = supabase.table("issues").select("*").execute()
    issues = response.data
    
    if not issues:
        print("✅ Database is empty. Nothing to clean.")
        return
        
    print(f"📊 Found {len(issues)} issues in the database.\n")
    
    ids_to_delete = []
    reasons_map = {}
    
    # Pre-fetch all unique repos to avoid blocking the main loop
    unique_repos = list(set(issue.get('repo_name') for issue in issues if issue.get('repo_name')))
    print(f"🌐 Fetching context for {len(unique_repos)} unique repositories...")
    
    repo_cache = {}
    for i, repo in enumerate(unique_repos):
        sys.stdout.write(f"\r   [{i+1}/{len(unique_repos)}] Fetching {repo}...")
        sys.stdout.flush()
        repo_cache[repo] = get_repo_context_from_name(repo)
        time.sleep(0.1)
    print("\n✅ All repo contexts loaded!\n")
    
    for i, issue in enumerate(issues):
        issue_id = issue['id']
        title = issue.get('title', '')
        ai_hint = issue.get('ai_hint', '')
        repo_name = issue.get('repo_name', '')
        
        sys.stdout.write(f"\r🔍 Analyzing issue {i+1}/{len(issues)}...")
        sys.stdout.flush()
        
        # A. Pre-Filter Check
        pf_result = pre_filter_issue_from_csv(title, ai_hint)
        if not pf_result['pass']:
            ids_to_delete.append(issue_id)
            reasons_map[issue_id] = f"Pre-filter fail: {pf_result['reason']}"
            continue
            
        repo_ctx = repo_cache.get(repo_name, {})
        repo_language = repo_ctx.get('language', 'Unknown')
        
        # C. Post-Validator Check (Anti-Hallucination)
        valid, failures = validate_llama_output(ai_hint, repo_language)
        if not valid:
            ids_to_delete.append(issue_id)
            reasons_map[issue_id] = f"Template Collapse / Hallucination: {failures[0]}"
            continue
            
        # D. Quality Score Check
        quality = compute_quality_score(ai_hint, repo_ctx)
        if quality['grade'] in ['Low', 'Medium']:
            # We can be aggressive and delete Medium too, or just Low. Let's delete Low and bottom-tier Medium.
            if quality['overall'] < 60:
                ids_to_delete.append(issue_id)
                reasons_map[issue_id] = f"Low Quality Score: {quality['overall']} ({quality['grade']})"
                continue

    print(f"\n\n🗑️ Evaluated all issues. Found {len(ids_to_delete)} issues to delete.")
    
    if not ids_to_delete:
        print("✨ Database is already perfectly clean!")
        return
        
    print("⏳ Deleting bad issues...")
    
    # Print a tiny sample of what we are deleting to the console
    print("\nSample of issues being deleted:")
    for del_id in ids_to_delete[:5]:
        print(f"   - ID {del_id}: {reasons_map[del_id]}")
    if len(ids_to_delete) > 5:
        print(f"   ...and {len(ids_to_delete) - 5} more.\n")
    
    deleted_count = 0
    batch_size = 50
    
    for i in range(0, len(ids_to_delete), batch_size):
        batch = ids_to_delete[i:i+batch_size]
        try:
            response = supabase.table("issues").delete().in_("id", batch).execute()
            deleted_count += len(response.data) if response.data else len(batch)
            print(f"   ✓ Deleted {min(i+batch_size, len(ids_to_delete))}/{len(ids_to_delete)}")
        except Exception as e:
            print(f"❌ Error deleting batch: {e}")
            
    print(f"\n🎉 Clean-up complete! Deleted {deleted_count} hallucinated/low-quality issues.")

if __name__ == "__main__":
    clean_database()
