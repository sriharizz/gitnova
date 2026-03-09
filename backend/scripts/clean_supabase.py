"""
GitNova Supabase Cleaner
========================
Reads the filtered output CSV and deletes all issues from Supabase
that failed the pre-filter, post-validation, or scored < 40 (Low Quality).
"""

import os
import sys
import csv
from supabase import create_client
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("❌ CRITICAL: Supabase credentials missing from .env")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def clean_supabase_db():
    input_file = os.path.expanduser("~/Downloads/supabase_latest_export_filtered.csv")
    
    if not os.path.exists(input_file):
        print(f"❌ Cannot find filtered CSV at: {input_file}")
        sys.exit(1)
        
    ids_to_delete = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Delete if it failed pre-filter or post-validation, OR if quality is Low
            if row.get('filter_status') in ['DROP', 'FLAGGED'] or row.get('quality_grade') == 'Low':
                ids_to_delete.append(row['id'])

    print(f"🗑️ Found {len(ids_to_delete)} bad issues to delete from Supabase.")
    
    if not ids_to_delete:
        print("✅ Database is already clean!")
        return
        
    print("⏳ Deleting in batches...")
    
    # Delete in batches of 100 to avoid request URL length limits
    batch_size = 100
    deleted_count = 0
    
    for i in range(0, len(ids_to_delete), batch_size):
        batch = ids_to_delete[i:i+batch_size]
        try:
            # supabase-py requires eq on id. To delete multiple, we use in_
            response = supabase.table("issues").delete().in_("id", batch).execute()
            deleted_count += len(response.data) if response.data else len(batch)
            print(f"   ...deleted {min(i+batch_size, len(ids_to_delete))}/{len(ids_to_delete)}")
        except Exception as e:
            print(f"❌ Error deleting batch: {e}")
            
    print(f"\n✅ Clean-up complete! Deleted {deleted_count} low-quality issues from Supabase.")

if __name__ == "__main__":
    clean_supabase_db()
