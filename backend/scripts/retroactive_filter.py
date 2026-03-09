"""
GitNova Retroactive CSV Filter
================================
Applies the new pipeline's pre-filter + post-validation + quality scoring
to the EXISTING issues_rows CSV export from Supabase.

Usage:
    cd backend
    python -m scripts.retroactive_filter

Input:  ~/Downloads/issues_rows (7).csv  (943 rows)
Output: ~/Downloads/issues_rows_filtered.csv (with quality_score + grade + filter_status columns)
"""

import os
import sys
import csv
import re
import time

# Add the backend directory to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.pipeline.pre_filter import pre_filter_issue_from_csv
from app.pipeline.post_validator import validate_hint_from_csv
from app.pipeline.quality_scorer import compute_quality_score
from app.pipeline.repo_grounding import get_repo_context_from_name


def run_retroactive_filter():
    # --- Config ---
    downloads_dir = os.path.expanduser("~/Downloads")
    input_file = os.path.join(downloads_dir, "supabase_latest_export.csv")
    output_file = os.path.join(downloads_dir, "supabase_latest_export_filtered.csv")
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    print(f"📂 Input:  {input_file}")
    print(f"📂 Output: {output_file}")
    print()
    
    # --- Read CSV ---
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    print(f"📊 Loaded {len(rows)} rows")
    print()
    
    # --- Track stats ---
    stats = {
        "total": len(rows),
        "pre_filter_dropped": 0,
        "post_validation_failed": 0,
        "kept": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    
    # --- Repo context cache ---
    repo_cache = {}
    repos_to_fetch = list(set(row.get('repo_name', '') for row in rows if row.get('repo_name')))
    
    print(f"🌐 Fetching repo context for {len(repos_to_fetch)} unique repos...")
    for i, repo in enumerate(repos_to_fetch):
        if repo:
            ctx = get_repo_context_from_name(repo)
            repo_cache[repo] = ctx
            lang = ctx.get('language', '?')
            sys.stdout.write(f"\r   [{i+1}/{len(repos_to_fetch)}] {repo}: {lang}     ")
            sys.stdout.flush()
            time.sleep(0.1)  # Be gentle with GitHub API
    
    print(f"\n   ✅ All repo contexts loaded.\n")
    
    # --- Process each row ---
    output_rows = []
    output_fieldnames = list(fieldnames) + ['quality_score', 'quality_grade', 'filter_status', 'filter_reason']
    
    for i, row in enumerate(rows):
        title = row.get('title', '')
        ai_hint = row.get('ai_hint', '')
        repo_name = row.get('repo_name', '')
        
        # Default values
        row['filter_status'] = 'KEEP'
        row['filter_reason'] = ''
        row['quality_score'] = ''
        row['quality_grade'] = ''
        
        # --- Pre-filter ---
        pf_result = pre_filter_issue_from_csv(title, ai_hint)
        if not pf_result['pass']:
            row['filter_status'] = 'DROP'
            row['filter_reason'] = pf_result['reason']
            stats['pre_filter_dropped'] += 1
            output_rows.append(row)
            continue
        
        # --- Post-validation ---
        repo_ctx = repo_cache.get(repo_name, {})
        valid, failures = validate_hint_from_csv(ai_hint, repo_name, repo_ctx)
        if not valid:
            row['filter_status'] = 'FLAGGED'
            row['filter_reason'] = '; '.join(failures)
            stats['post_validation_failed'] += 1
        
        # --- Quality scoring ---
        quality = compute_quality_score(ai_hint, repo_ctx)
        row['quality_score'] = str(quality['overall'])
        row['quality_grade'] = quality['grade']
        
        if quality['grade'] == 'High':
            stats['high'] += 1
        elif quality['grade'] == 'Medium':
            stats['medium'] += 1
        else:
            stats['low'] += 1
        
        stats['kept'] += 1
        output_rows.append(row)
        
        # Progress update
        if (i + 1) % 100 == 0:
            print(f"   Processed {i+1}/{len(rows)} rows...")
    
    # --- Write output CSV ---
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    # --- Print summary ---
    print()
    print("=" * 60)
    print("📊 RETROACTIVE FILTER RESULTS")
    print("=" * 60)
    print(f"   📥 Total rows:            {stats['total']}")
    print(f"   🚫 Pre-filter dropped:    {stats['pre_filter_dropped']}")
    print(f"   ⚠️  Post-validation flagged: {stats['post_validation_failed']}")
    print(f"   ✅ Kept:                   {stats['kept']}")
    print()
    
    total_graded = stats['high'] + stats['medium'] + stats['low']
    if total_graded > 0:
        print(f"   🟢 High Quality (≥70):    {stats['high']} ({stats['high']/total_graded*100:.1f}%)")
        print(f"   🟡 Medium Quality (40-69): {stats['medium']} ({stats['medium']/total_graded*100:.1f}%)")
        print(f"   🔴 Low Quality (<40):     {stats['low']} ({stats['low']/total_graded*100:.1f}%)")
    
    print()
    print(f"   📂 Output saved to: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    run_retroactive_filter()
