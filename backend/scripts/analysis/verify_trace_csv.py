import csv
from pathlib import Path

csv_path = Path("c:/gitNova/traces/runs/2026-08-16T18-32-17Z_b94d3c/trace.csv")

with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"trace.csv successfully loaded {len(rows)} rows.")
print(f"Columns ({len(reader.fieldnames)}): {reader.fieldnames}")
print(f"Sample row 1 (Flexify #332):")
for k, v in [r for r in rows if r["issue_number"] == "332"][0].items():
    print(f"  {k}: {v}")
