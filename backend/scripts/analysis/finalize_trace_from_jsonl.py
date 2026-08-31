import json
import csv
from pathlib import Path
import sys

backend_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_path))

from app.pipeline.pipeline_tracer import PipelineTracer

run_dir = Path("c:/gitNova/traces/runs/2026-08-16T18-32-17Z_b94d3c")
jsonl_path = run_dir / "trace.jsonl"

records = []
trace_map = {}
with open(jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            t_id = data.get("trace_id")
            if t_id:
                # Merge sequential updates for same trace_id
                if t_id not in trace_map:
                    trace_map[t_id] = data
                else:
                    # Update fields
                    for k, v in data.items():
                        if v is not None:
                            trace_map[t_id][k] = v
        except Exception as e:
            print(f"Error parsing line: {e}")

print(f"Loaded {len(trace_map)} unique issue traces from trace.jsonl.")

# Create tracer with run_id and populate trace_records
tracer = PipelineTracer(run_id="2026-08-16T18-32-17Z_b94d3c")
tracer.trace_records = trace_map

summary = tracer.finish_run()
print(f"Generated summary.json, summary.md, and trace.csv in {run_dir}")
print(json.dumps(summary, indent=2))
