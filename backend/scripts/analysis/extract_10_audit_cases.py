import json
from pathlib import Path

jsonl_path = Path("c:/gitNova/traces/runs/2026-08-16T18-32-17Z_b94d3c/trace.jsonl")

gemini_cases = []
with open(jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        rec = json.loads(line.strip())
        if (rec.get("stage_6_gemini") or {}).get("called") is True:
            gemini_cases.append(rec)

print(f"Total Gemini Cases Found: {len(gemini_cases)}")

# Select 10 distinct issues representing all tiers & outcomes:
# 1. BEGINNER Published: brandonp2412/Flexify#332
# 2. BEGINNER Published: pallets/click#3696
# 3. BEGINNER+ Published: pallets/click#3652
# 4. BEGINNER Rejected (CVE): expressjs/express#7391
# 5. BEGINNER Rejected (Grounding Fail): Nike-Inc/hal#142
# 6. BEGINNER+ Rejected (Assigned/Available): eclipse-apoapsis/ort-server#5716
# 7. BEGINNER+ Rejected (Grounding Fail): apache/trafficserver#13555
# 8. INTERMEDIATE Rejected (Code Complexity): babalae/better-genshin-impact#3471
# 9. INTERMEDIATE Rejected (Multi-file / DB): brandonp2412/Flexify#331
# 10. ADVANCED Rejected (Shaded Libs): alibaba/nacos#15709

selected_keys = [
    ("brandonp2412/Flexify", 332),
    ("pallets/click", 3696),
    ("pallets/click", 3652),
    ("expressjs/express", 7391),
    ("Nike-Inc/hal", 142),
    ("eclipse-apoapsis/ort-server", 5716),
    ("apache/trafficserver", 13555),
    ("babalae/better-genshin-impact", 3471),
    ("brandonp2412/Flexify", 331),
    ("alibaba/nacos", 15709)
]

selected_traces = []
for repo, num in selected_keys:
    matching = [r for r in gemini_cases if r.get("repository") == repo and r.get("github_issue_number") == num]
    if matching:
        selected_traces.append(matching[-1])

print(f"Selected {len(selected_traces)} balanced distinct cases for audit.")

output_data = []
for idx, r in enumerate(selected_traces, 1):
    s3 = r.get("stage_3_repository_context") or {}
    s4 = r.get("stage_4_rag") or {}
    s5 = r.get("stage_5_evidence") or {}
    s6 = r.get("stage_6_gemini") or {}
    s7 = r.get("stage_7_grounding") or {}
    s8 = r.get("stage_8_publication") or {}
    s9 = r.get("stage_9_database") or {}

    item = {
        "index": idx,
        "repo": r.get("repository"),
        "issue_number": r.get("github_issue_number"),
        "title": r.get("title"),
        "url": r.get("github_url"),
        "language": r.get("language"),
        "body_length": r.get("body_length"),
        "labels": r.get("labels"),
        "state": r.get("final_state"),
        "difficulty_tier": s6.get("difficulty_tier"),
        "publication_decision": s6.get("publication_decision"),
        "availability": s6.get("availability"),
        "suitability": s6.get("suitability"),
        "retrieved_files": s4.get("retrieved_files", []),
        "retrieved_symbols": s4.get("retrieved_symbols", []),
        "vector_count": s4.get("vector_count"),
        "lexical_count": s4.get("lexical_count"),
        "rrf_count": s4.get("rrf_count"),
        "latency_ms": s6.get("latency_ms"),
        "model": s6.get("model"),
        "grounding_status": s7.get("decision"),
        "gate_status": s8.get("final_gate"),
        "failed_criteria": s8.get("failed_criteria"),
        "rejection_reasons": s8.get("rejection_reasons"),
    }
    output_data.append(item)

print(json.dumps(output_data, indent=2))
