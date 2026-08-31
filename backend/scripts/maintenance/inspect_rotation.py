import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from supabase import create_client
from app.core.config import settings
from app.pipeline.run_issue_sync import get_rotated_repositories

sb = create_client(settings.supabase_url, settings.supabase_key)
repos, curr_offset, next_offset, total = get_rotated_repositories(sb, max_repos=25)
print(f"Current offset: {curr_offset}, Next offset: {next_offset}, Total active: {total}")
for i, r in enumerate(repos):
    print(f"  [{i+1}] {r.get('full_name')} ({r.get('language')}) score={r.get('score')}")
