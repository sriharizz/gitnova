import sys
import time
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from app.pipeline.run_issue_sync import run_12h_incremental_sync
from app.pipeline.pipeline_tracer import get_current_tracer

print("🚀 Launching GitNova Diagnostic Funnel Experiment (~40 Raw Candidate Population)...")
print("================================================================================")

start_time = time.time()
res = run_12h_incremental_sync(
    dry_run=True,
    max_repos=25,
    max_candidates_per_repo=5,
    max_pages_per_repo=2,
    lookback_hours=168  # 7-day window to capture natural ~40 raw candidate pool across 25 rotated repos
)

elapsed = round(time.time() - start_time, 2)
tracer = get_current_tracer()

print("\n================================================================================")
print(f"🎉 Experiment Completed in {elapsed}s.")
if tracer:
    print(f"📁 Run ID: {tracer.run_id}")
    print(f"📊 Traces written to: {tracer.run_dir}")
    print(f"   - {tracer.csv_path}")
    print(f"   - {tracer.jsonl_path}")
    print(f"   - {tracer.summary_json_path}")
    print(f"   - {tracer.summary_md_path}")
print("================================================================================")
