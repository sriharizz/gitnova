"""
GitNova Supabase Exporter
=========================
Exports the latest 'issues' table data from Supabase to a CSV file
for retroactive filtering.
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

def export_latest_issues():
    output_file = os.path.join(os.path.expanduser("~/Downloads"), "supabase_latest_export.csv")
    
    print("📥 Fetching issues from Supabase...")
    try:
        # We need to use pagination if there are more than 1000 rows, 
        # but let's try grabbing a large chunk first or paginate.
        all_data = []
        page_size = 1000
        start = 0
        
        while True:
            response = supabase.table("issues").select("*").range(start, start + page_size - 1).execute()
            data = response.data
            if not data:
                break
            all_data.extend(data)
            print(f"   ...fetched {len(all_data)} rows so far")
            if len(data) < page_size:
                break
            start += page_size
            
        if not all_data:
            print("⚠️ No issues found in the database.")
            return

        print(f"✅ Total fetched: {len(all_data)} rows.")
        
        # Write to CSV
        fieldnames = list(all_data[0].keys())
        # Ensure we have the same key names we expect in the retroactive filter
        # The filter looks for: repo_name, title, ai_hint
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)
            
        print(f"💾 Exported to: {output_file}")

    except Exception as e:
        print(f"❌ Error fetching from Supabase: {e}")

if __name__ == "__main__":
    export_latest_issues()
