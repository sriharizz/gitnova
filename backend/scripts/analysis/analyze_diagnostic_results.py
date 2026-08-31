import json
import csv
from pathlib import Path

run_dir = Path("c:/gitNova/traces/runs/2026-08-16T18-32-17Z_b94d3c")
jsonl_path = run_dir / "trace.jsonl"
csv_path = run_dir / "trace.csv"

records = []
with open(jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line.strip()))

# De-duplicate by trace_id (latest record wins)
trace_dict = {}
for r in records:
    trace_dict[r["trace_id"]] = r

all_traces = list(trace_dict.values())
print(f"Total Unique Traces: {len(all_traces)}")

# Analyze Stage 1: Repositories & Languages
repo_counts = {}
lang_counts = {}
for r in all_traces:
    repo = r.get("repository", "unknown")
    lang = r.get("language", "unknown")
    repo_counts[repo] = repo_counts.get(repo, 0) + 1
    lang_counts[lang] = lang_counts.get(lang, 0) + 1

print("\n--- REPOSITORIES DISCOVERED ---")
for repo, count in sorted(repo_counts.items(), key=lambda x: -x[1]):
    print(f"  {repo}: {count} candidates")

print("\n--- LANGUAGES DISCOVERED ---")
for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
    print(f"  {lang}: {count} candidates")

# Analyze Stage 2: Deterministic Rejections vs Passes
s2_passed = [r for r in all_traces if (r.get("stage_2_prefilter") or {}).get("decision") == "PASS"]
s2_rejected = [r for r in all_traces if (r.get("stage_2_prefilter") or {}).get("decision") == "REJECT"]

print(f"\n--- STAGE 2 BREAKDOWN ---")
print(f"  Passed: {len(s2_passed)}")
print(f"  Rejected: {len(s2_rejected)}")

s2_rules = {}
for r in s2_rejected:
    rule = (r.get("stage_2_prefilter") or {}).get("rule_id", "UNKNOWN")
    s2_rules[rule] = s2_rules.get(rule, 0) + 1

for rule, count in s2_rules.items():
    print(f"    {rule}: {count}")

# Print all non-PR Stage 2 rejections for False-Negative Audit
print("\n--- NON-PR STAGE 2 REJECTIONS FOR AUDIT ---")
for r in s2_rejected:
    rule = (r.get("stage_2_prefilter") or {}).get("rule_id")
    if rule != "PULL_REQUEST":
        print(f"[{rule}] {r['repository']}#{r['github_issue_number']} - {r['title']} (body len: {r.get('body_length')})")
        print(f"  Reason: {(r.get('stage_2_prefilter') or {}).get('reason')}")
        print(f"  URL: {r.get('github_url')}")

# Print sample of PR rejections for False-Negative Audit
print("\n--- SAMPLE OF PR STAGE 2 REJECTIONS FOR AUDIT ---")
pr_sample = [r for r in s2_rejected if (r.get("stage_2_prefilter") or {}).get("rule_id") == "PULL_REQUEST"][:10]
for r in pr_sample:
    title_safe = r['title'].encode('ascii', errors='replace').decode('ascii')
    print(f"[PULL_REQUEST] {r['repository']}#{r['github_issue_number']} - {title_safe}")

# Analyze Gemini Evaluated Population
gemini_records = [r for r in all_traces if (r.get("stage_6_gemini") or {}).get("called") is True]
print(f"\n--- GEMINI EVALUATED POPULATION ({len(gemini_records)} issues) ---")
for r in gemini_records:
    g = r.get("stage_6_gemini") or {}
    s8 = r.get("stage_8_publication") or {}
    s7 = r.get("stage_7_grounding") or {}
    print(f"Issue: {r['repository']}#{r['github_issue_number']} | State: {r.get('final_state')} | Diff: {g.get('difficulty_tier')} | PubDecision: {g.get('publication_decision')} | Grounding: {(s7.get('decision'))} | S8Gate: {(s8.get('final_gate'))}")
    if s8.get("final_gate") == "FAIL":
        print(f"  Gate Failed Criteria: {s8.get('failed_criteria')}")
        print(f"  Rejection Reasons: {s8.get('rejection_reasons')}")
