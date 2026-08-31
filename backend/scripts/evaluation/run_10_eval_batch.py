import os
import sys
import json
import time

sys.path.insert(0, 'backend')
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

from dotenv import load_dotenv
from supabase import create_client
from app.pipeline.github_client import GitHubClient
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline

load_dotenv('backend/.env')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

supabase = create_client(supabase_url, supabase_key)
github = GitHubClient(supabase_client=supabase)

candidates = [
    {"repo": "spf13/cobra", "number": 2477, "lang": "Go"},
    {"repo": "clap-rs/clap", "number": 6485, "lang": "Rust"},
    {"repo": "microcks/microcks", "number": 2273, "lang": "Java"},
    {"repo": "scikit-learn/scikit-learn", "number": 34736, "lang": "Python/C++"},
    {"repo": "medusajs/medusa", "number": 16463, "lang": "TypeScript"},
    {"repo": "kubescape/kubescape", "number": 3293, "lang": "Go"},
    {"repo": "ente/ente", "number": 12219, "lang": "TypeScript"},
    {"repo": "andreknieriem/open-headunit", "number": 840, "lang": "C/C++"},
    {"repo": "zulip/zulip-terminal", "number": 1644, "lang": "Python"},
    {"repo": "runtipi/runtipi", "number": 2622, "lang": "TypeScript"}
]

print(f"🚀 Running GitNova v2 Canonical Pipeline on {len(candidates)} diverse candidate issues...\n")

results = []

for idx, item in enumerate(candidates, 1):
    repo = item["repo"]
    num = item["number"]
    lang = item["lang"]
    print(f"[{idx}/{len(candidates)}] Processing {repo} #{num} ({lang})...")
    
    try:
        res = CanonicalIngestionPipeline.ingest_and_process_issue(
            repo_full_name=repo,
            github_issue_number=num,
            supabase_client=supabase,
            github_client=github,
            dry_run=True
        )
        results.append({
            "index": idx,
            "repo": repo,
            "number": num,
            "lang": lang,
            "result": res
        })
        print(f"   -> Result: published={res.get('published')} | diff={res.get('difficulty_tier')} | verif={res.get('verification_status')}\n")
    except Exception as err:
        print(f"   ❌ Error processing {repo} #{num}: {err}\n")
        results.append({
            "index": idx,
            "repo": repo,
            "number": num,
            "lang": lang,
            "error": str(err)
        })
    
    # 2-second rate-limit spacing
    time.sleep(2)

print("📝 Generating EVALUATION_10_BATCH_RESULTS.md...")

md = []
md.append("# GitNova v2 Evaluation Report: 10 Fresh Issues Across 10 Repositories\n\n")
md.append(f"> **Evaluation Run Date:** `2026-08-16` | **Batch Size:** `10 Issues from 10 Distinct Repositories` | **Pipeline Mode:** `Exact Production GitNova v2 (dry_run=True)`\n\n")

md.append("This document contains the complete evidence, Gemini investigation decisions, grounded AST code citations, guided plans, and 10-point fail-closed gating verdicts for the 10 fresh evaluation candidates.\n\n")

md.append("## 📊 Summary Table\n\n")
md.append("| # | Repository | Issue # | Language | LLM Difficulty | Availability Status | Grounding Status | Gate Verdict |\n")
md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")

for r in results:
    idx = r["index"]
    repo = r["repo"]
    num = r["number"]
    lang = r["lang"]
    res = r.get("result", {})
    if "error" in r:
        md.append(f"| **{idx}** | `{repo}` | `#{num}` | `{lang}` | `ERROR` | `ERROR` | `ERROR` | `FAILED` ❌ |\n")
        continue
    
    diff = res.get("difficulty_tier", "UNKNOWN")
    avail = res.get("availability_status", "UNKNOWN")
    verif = res.get("verification_status", "UNKNOWN")
    pub = "**`PUBLISHED`** ✅" if res.get("published") else "**`GATED / REJECTED`** 🛡️"
    
    md.append(f"| **{idx}** | `{repo}` | `#{num}` | `{lang}` | `{diff}` | `{avail}` | `{verif}` | {pub} |\n")

md.append("\n---\n\n")
md.append("## 📦 Detailed Issue Investigation & Generated Content\n\n")

for r in results:
    idx = r["index"]
    repo = r["repo"]
    num = r["number"]
    lang = r["lang"]
    res = r.get("result", {})
    
    if "error" in r:
        md.append(f"### {idx}. {repo} #{num} ({lang})\n\n")
        md.append(f"❌ **Pipeline Execution Error:** `{r['error']}`\n\n---\n\n")
        continue

    title = res.get("title", "N/A")
    pub = res.get("published", False)
    pub_badge = "🟢 PUBLISHED LIVE" if pub else "🛡️ REJECTED / GATED (published=False)"
    diff = res.get("difficulty_tier", "UNKNOWN")
    avail = res.get("availability_status", "UNKNOWN")
    verif = res.get("verification_status", "UNKNOWN")
    suit_score = res.get("suitability_score", 75)
    
    exp = res.get("explanation", {})
    if isinstance(exp, str):
        try:
            exp = json.loads(exp)
        except Exception:
            exp = {}
            
    summary = exp.get("summary") or "No summary generated."
    why = exp.get("why_it_happens") or "No root cause generated."
    concepts = exp.get("structured_concepts") or exp.get("prerequisite_concepts") or []
    locations = exp.get("relevant_locations") or []
    plan = exp.get("step_by_step_plan") or []
    pitfalls = exp.get("common_pitfalls") or []
    
    llm_diff_reason = exp.get("difficulty_reasoning") or "N/A"
    llm_avail_reason = exp.get("availability_reasoning") or "N/A"
    llm_pub_decision = exp.get("publication_decision") or "N/A"
    llm_pub_reason = exp.get("publication_reason") or "N/A"
    verif_reasons = exp.get("verification_reasons") or []

    md.append(f"### {idx}. [{repo} #{num}](https://github.com/{repo}/issues/{num}): {title}\n\n")
    md.append(f"- **Language / Ecosystem:** `{lang}`\n")
    md.append(f"- **Final Publication Gate Verdict:** **{pub_badge}**\n")
    md.append(f"- **Difficulty Tier:** `{diff}` (Suitability Score: `{suit_score}/100`)\n")
    md.append(f"- **GitHub Availability Status:** `{avail}`\n")
    md.append(f"- **AST Grounding Status:** `{verif}`\n\n")

    md.append("#### 🤖 1. Gemini Investigation & Gating Decisions\n")
    md.append(f"- **LLM Difficulty Assessment:** `{diff}` — *{llm_diff_reason}*\n")
    md.append(f"- **LLM Availability Assessment:** `{exp.get('availability', 'N/A')}` — *{llm_avail_reason}*\n")
    md.append(f"- **LLM Publication Decision:** `{llm_pub_decision}` — *{llm_pub_reason}*\n\n")

    md.append("#### 📋 2. Plain-English Summary\n")
    md.append(f"> {summary}\n\n")

    md.append("#### 🔍 3. Technical Root Cause (`why_it_happens`)\n")
    md.append(f"> {why}\n\n")

    md.append("#### 🎓 4. Prerequisite Educational Concepts\n")
    if concepts:
        for c in concepts:
            if isinstance(c, dict):
                c_name = c.get("concept_name", "Concept")
                c_expl = c.get("short_explanation", "")
                c_why = c.get("why_it_matters", "")
                c_conn = c.get("connection_to_issue", "")
                md.append(f"- **{c_name}:** {c_expl}\n")
                if c_why:
                    md.append(f"  - *Why it matters:* {c_why}\n")
                if c_conn:
                    md.append(f"  - *Connection to this issue:* {c_conn}\n")
            else:
                md.append(f"- **{c}**\n")
    else:
        md.append("*None generated.*\n")
    md.append("\n")

    md.append("#### 📍 5. Grounded Code Citations\n")
    if locations:
        for loc in locations:
            fpath = loc.get("file_path", "N/A")
            sym = loc.get("symbol_name", "N/A")
            lines = loc.get("lines", "N/A")
            role = loc.get("role", "Relevant Code")
            ver = "✅ Grounded" if loc.get("is_verified") else "⚠️ Unverified"
            md.append(f"- `{fpath}` (`{sym}`, Lines {lines}) — *{role}* ({ver})\n")
    else:
        md.append("*No code locations cited.*\n")
    md.append("\n")

    md.append("#### 🛠️ 6. Step-by-Step Guided Plan\n")
    if plan:
        for p in plan:
            num_step = p.get("step_number", "")
            p_title = p.get("title", "")
            p_desc = p.get("description", "")
            p_file = p.get("target_file", "")
            file_str = f" [Target: `{p_file}`]" if p_file else ""
            md.append(f"{num_step}. **{p_title}**{file_str}: {p_desc}\n")
    else:
        md.append("*No plan generated.*\n")
    md.append("\n")

    md.append("#### ⚠️ 7. Common Pitfalls\n")
    if pitfalls:
        for pit in pitfalls:
            md.append(f"- {pit}\n")
    else:
        md.append("*None listed.*\n")
    md.append("\n")

    if verif_reasons:
        md.append("#### 🛡️ 8. Grounding Verification Audit Notes\n")
        for vr in verif_reasons:
            md.append(f"- {vr}\n")
        md.append("\n")

    md.append("---\n\n")

with open("EVALUATION_10_BATCH_RESULTS.md", "w", encoding="utf-8") as f:
    f.writelines(md)

print("🎉 SUCCESS: EVALUATION_10_BATCH_RESULTS.md generated successfully.")
