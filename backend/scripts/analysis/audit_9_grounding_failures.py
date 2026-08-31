import json
from pathlib import Path

jsonl_path = Path("c:/gitNova/traces/runs/2026-08-16T18-32-17Z_b94d3c/trace.jsonl")

grounding_fails = []
with open(jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        rec = json.loads(line.strip())
        s6 = rec.get("stage_6_gemini") or {}
        s7 = rec.get("stage_7_grounding") or {}
        s8 = rec.get("stage_8_publication") or {}
        if s6.get("called") is True and s7.get("decision") == "FAIL":
            grounding_fails.append(rec)

print(f"Total Grounding Failures Found: {len(grounding_fails)}")
for idx, r in enumerate(grounding_fails, 1):
    s4 = r.get("stage_4_rag") or {}
    s6 = r.get("stage_6_gemini") or {}
    s7 = r.get("stage_7_grounding") or {}
    print(f"\n--- [{idx}] {r['repository']}#{r['github_issue_number']} ---")
    print(f"  Title: {r['title']}")
    print(f"  Language: {r.get('language')}")
    print(f"  Grounding Reason: {s7.get('reason')}")
    print(f"  Retrieved Files ({len(s4.get('retrieved_files', []))}): {s4.get('retrieved_files')}")
    print(f"  Retrieved Symbols ({len(s4.get('retrieved_symbols', []))}): {s4.get('retrieved_symbols')}")
    print(f"  Difficulty: {s6.get('difficulty_tier')}")
