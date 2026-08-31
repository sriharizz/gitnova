import os
import sys
import json
import csv
import time
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict, Counter

backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from supabase import create_client
from app.pipeline.github_client import GitHubClient
from app.pipeline.pre_filter import pre_filter_issue


# ── ISSUE TYPE TAXONOMY MAPPER (FOR AUDIT METADATA ONLY) ──────────────────────
def classify_issue_type(title: str, body: str, labels: List[Dict[str, Any]]) -> str:
    """Classifies issue into standard descriptive categories based on labels and title."""
    label_names = [lbl.get("name", "").lower() if isinstance(lbl, dict) else str(lbl).lower() for lbl in labels]
    label_str = " ".join(label_names)
    text_lower = f"{title.lower()} {body.lower()[:300]}"

    if any(k in label_str for k in ["bug", "defect", "fault", "crash", "error", "fix", "regression"]):
        return "bug"
    if any(k in label_str for k in ["enhancement", "feature", "new feature", "feat"]):
        return "enhancement"
    if any(k in label_str for k in ["doc", "documentation", "typo", "readme"]):
        return "documentation"
    if any(k in label_str for k in ["test", "testing", "unit-test", "e2e", "coverage"]):
        return "testing"
    if any(k in label_str for k in ["refactor", "cleanup", "clean up", "restructure"]):
        return "refactor"
    if any(k in label_str for k in ["perf", "performance", "speed", "memory", "leak", "optimize"]):
        return "performance"
    if any(k in label_str for k in ["ci", "build", "actions", "workflow", "docker", "pipeline"]):
        return "build/CI"
    if any(k in label_str for k in ["security", "cve", "vulnerability", "auth"]):
        return "security"
    if any(k in label_str for k in ["question", "help wanted", "discussion", "support"]):
        return "question"
    if any(k in label_str for k in ["proposal", "rfc", "design", "roadmap", "plan"]):
        return "RFC/proposal"
    if any(k in label_str for k in ["dep", "dependency", "bump", "upgrade", "dependencies"]):
        return "dependency"
    if any(k in label_str for k in ["ui", "ux", "frontend", "style", "theme", "css", "layout"]):
        return "UI"
    if any(k in label_str for k in ["config", "configuration", "settings", "env"]):
        return "configuration"

    # Fallback to title keywords
    if any(k in text_lower for k in ["bug", "error", "fails", "failed", "crash", "exception", "broken", "panic"]):
        return "bug"
    if any(k in text_lower for k in ["feature", "support", "add", "allow", "implement", "request"]):
        return "enhancement"
    if any(k in text_lower for k in ["doc", "readme", "guide", "tutorial", "typo"]):
        return "documentation"
    if any(k in text_lower for k in ["test", "coverage", "mock"]):
        return "testing"
    if any(k in text_lower for k in ["refactor", "clean", "simplify"]):
        return "refactor"
    if any(k in text_lower for k in ["speed", "slow", "perf", "latency", "benchmark"]):
        return "performance"
    if any(k in text_lower for k in ["build", "ci", "cmake", "maven", "gradle", "action"]):
        return "build/CI"
    if any(k in text_lower for k in ["proposal", "rfc", "idea"]):
        return "RFC/proposal"
    if any(k in text_lower for k in ["ui", "layout", "button", "theme", "color", "icon"]):
        return "UI"
    if any(k in text_lower for k in ["upgrade", "bump", "version", "depend"]):
        return "dependency"

    return "other"


def perform_phase1_audit(raw_jsonl_path: Path, audit_dir: Path) -> Dict[str, Any]:
    """Audits raw v1 dataset, separating PRs from real issues."""
    audit_dir.mkdir(parents=True, exist_ok=True)
    raw_records = []
    with open(raw_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                raw_records.append(json.loads(line.strip()))

    total_records = len(raw_records)
    prs = [r for r in raw_records if r.get("is_pull_request") is True]
    real_issues = [r for r in raw_records if r.get("is_pull_request") is False]

    # Issue type breakdown
    issue_types = Counter(classify_issue_type(r.get("title", ""), r.get("body", ""), r.get("labels", [])) for r in real_issues)

    # Repository breakdown
    repo_counts = Counter(r["repo_name"] for r in real_issues)
    lang_counts = Counter(r["repo_language"] for r in real_issues)

    # Content length & metrics
    body_word_counts = [len((r.get("body") or "").split()) for r in real_issues]
    avg_words = sum(body_word_counts) / len(body_word_counts) if body_word_counts else 0
    sorted_words = sorted(body_word_counts)
    median_words = sorted_words[len(sorted_words) // 2] if sorted_words else 0
    short_content = sum(1 for w in body_word_counts if w < 20)
    long_content = sum(1 for w in body_word_counts if w > 500)
    missing_bodies = sum(1 for w in body_word_counts if w == 0)
    missing_titles = sum(1 for r in real_issues if not (r.get("title") or "").strip())
    issues_with_comments = sum(1 for r in real_issues if (r.get("comments_count") or 0) > 0)

    # Temporal analysis
    created_dates = [r.get("created_at") for r in real_issues if r.get("created_at")]
    created_dates.sort()
    oldest_issue = created_dates[0] if created_dates else "None"
    newest_issue = created_dates[-1] if created_dates else "None"

    # Pre-filter decisions
    prefilter_decisions = Counter(r.get("existing_prefilter_decision") for r in real_issues)

    audit_summary = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_v1_counts": {
            "total_raw_records": total_records,
            "pull_requests_count": len(prs),
            "pull_requests_pct": round((len(prs) / total_records) * 100, 2) if total_records else 0,
            "real_issues_count": len(real_issues),
            "real_issues_pct": round((len(real_issues) / total_records) * 100, 2) if total_records else 0
        },
        "real_issues_metrics": {
            "unique_repositories": len(repo_counts),
            "unique_languages": len(lang_counts),
            "average_body_words": round(avg_words, 1),
            "median_body_words": median_words,
            "short_issues_count": short_content,
            "short_issues_pct": round((short_content / len(real_issues)) * 100, 2) if real_issues else 0,
            "long_issues_count": long_content,
            "long_issues_pct": round((long_content / len(real_issues)) * 100, 2) if real_issues else 0,
            "missing_bodies_count": missing_bodies,
            "missing_titles_count": missing_titles,
            "issues_with_comments_count": issues_with_comments,
            "issues_with_comments_pct": round((issues_with_comments / len(real_issues)) * 100, 2) if real_issues else 0,
            "oldest_issue_created_at": oldest_issue,
            "newest_issue_created_at": newest_issue
        },
        "distributions": {
            "issue_types": {k: {"count": cnt, "pct": round((cnt / len(real_issues)) * 100, 2)} for k, cnt in issue_types.most_common()},
            "languages": dict(lang_counts.most_common()),
            "prefilter_decisions": dict(prefilter_decisions),
            "top_repositories": dict(repo_counts.most_common(20))
        },
        "recommendation": "COLLECT_MORE_ISSUES" if len(real_issues) < 500 else "READY_FOR_LABELING"
    }

    # Save JSON report
    with open(audit_dir / "dataset_audit_v2.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)

    # Save Markdown report
    md_content = f"""# GitNova Dataset Audit Report (v2)

**Audit Date**: {audit_summary['audit_timestamp']}  
**Dataset Assessed**: `gitnova_raw_issues_v1.jsonl`

---

## 1. Population Overview

| Category | Count | Percentage |
| :--- | :--- | :--- |
| **Total Raw GitHub Records** | **{total_records}** | 100.0% |
| **Pull Requests (`is_pull_request: true`)** | **{len(prs)}** | {audit_summary['raw_v1_counts']['pull_requests_pct']}% |
| **Real GitHub Issues (`is_pull_request: false`)** | **{len(real_issues)}** | {audit_summary['raw_v1_counts']['real_issues_pct']}% |

> [!IMPORTANT]
> **Audit Finding**: Out of 650 raw records collected in v1, **258 are genuine GitHub issues**, while **392 are Pull Requests**.
> Because our target for candidate relevance fine-tuning is **500–700 REAL ISSUES**, we must collect an additional **~350 real issues** to reach our target.

---

## 2. Issue Type Distribution (Real Issues)

| Issue Type | Count | Share (%) |
| :--- | :--- | :--- |
"""
    for itype, data in audit_summary["distributions"]["issue_types"].items():
        md_content += f"| **{itype}** | {data['count']} | {data['pct']}% |\n"

    md_content += f"""
---

## 3. Real Issues Language Distribution

| Language | Real Issues | Share (%) |
| :--- | :--- | :--- |
"""
    for lang, cnt in audit_summary["distributions"]["languages"].items():
        pct = (cnt / len(real_issues)) * 100 if real_issues else 0
        md_content += f"| **{lang}** | {cnt} | {pct:.1f}% |\n"

    md_content += f"""
---

## 4. Content Quality & Freshness

- **Average Body Word Count**: {audit_summary['real_issues_metrics']['average_body_words']} words
- **Median Body Word Count**: {audit_summary['real_issues_metrics']['median_body_words']} words
- **Short Issues (<20 words)**: {audit_summary['real_issues_metrics']['short_issues_count']} ({audit_summary['real_issues_metrics']['short_issues_pct']}%)
- **Long Issues (>500 words)**: {audit_summary['real_issues_metrics']['long_issues_count']} ({audit_summary['real_issues_metrics']['long_issues_pct']}%)
- **Missing Bodies**: {audit_summary['real_issues_metrics']['missing_bodies_count']}
- **Missing Titles**: {audit_summary['real_issues_metrics']['missing_titles_count']}
- **Issues with Comments**: {audit_summary['real_issues_metrics']['issues_with_comments_count']} ({audit_summary['real_issues_metrics']['issues_with_comments_pct']}%)
- **Oldest Issue**: `{audit_summary['real_issues_metrics']['oldest_issue_created_at']}`
- **Newest Issue**: `{audit_summary['real_issues_metrics']['newest_issue_created_at']}`

---

## 5. Audit Decision

**Decision**: **`{audit_summary['recommendation']}`**  
*(Proceed to Phase 2 to collect additional real issues until total real issues reach 550–650).*
"""
    with open(audit_dir / "dataset_audit_v2.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📊 Phase 1 Audit Saved to {audit_dir / 'dataset_audit_v2.md'}")
    return audit_summary


def perform_phase2_expansion(
    target_real_issues: int = 600,
    per_repo_cap: int = 15,
    output_dir: Path = backend_path / "data" / "dataset_collection"
) -> Dict[str, Any]:
    """Expands dataset to reach target_real_issues using existing GitHub client and active repo pool."""
    print(f"\n🚀 Starting Phase 2: Expanding Real Issues to Target: {target_real_issues}...")
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    supabase = create_client(supabase_url, supabase_key)
    github = GitHubClient(supabase_client=supabase)

    # 1. Load existing raw v1 records
    raw_v1_path = output_dir / "gitnova_raw_issues_v1.jsonl"
    existing_real_items: Dict[Tuple[str, int], Dict[str, Any]] = {}
    repo_counts: Dict[str, int] = defaultdict(int)

    if raw_v1_path.exists():
        with open(raw_v1_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line.strip())
                    if rec.get("is_pull_request") is False:
                        key = (rec["repo_name"].lower(), int(rec["issue_number"]))
                        existing_real_items[key] = rec
                        repo_counts[rec["repo_name"]] += 1

    print(f"📦 Starting with {len(existing_real_items)} existing real issues from v1.")

    # 2. Fetch active repos and construct balanced rotation ring
    repos_resp = supabase.table("repos").select(
        "id, full_name, language, stars, forks, description, topics, is_active, score"
    ).eq("is_active", True).order("score", desc=True).execute()
    all_repos = repos_resp.data or []

    lang_buckets = defaultdict(list)
    for r in all_repos:
        lang = r.get("language") or "Other"
        lang_buckets[lang].append(r)

    rotation_ring = []
    max_depth = max((len(v) for v in lang_buckets.values()), default=0)
    for depth in range(max_depth):
        for lang in sorted(lang_buckets.keys()):
            bucket = lang_buckets[lang]
            if depth < len(bucket):
                rotation_ring.append(bucket[depth])

    # Cache Supabase issues table for observation fields
    sb_issues_map = {}
    try:
        sb_res = supabase.table("issues").select("repo_name, github_issue_number, difficulty_tier, difficulty, is_published").limit(1000).execute()
        for row in (sb_res.data or []):
            if row.get("repo_name") and row.get("github_issue_number"):
                sb_issues_map[(row["repo_name"].lower(), int(row["github_issue_number"]))] = row
    except Exception:
        pass

    run_id = f"run_v2_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
    start_time = time.time()
    pass_round = 1

    while len(existing_real_items) < target_real_issues and pass_round <= 10:
        print(f"\n🔄 --- Real Issue Collection Round {pass_round} (Current Real: {len(existing_real_items)}/{target_real_issues}) ---")
        added_in_round = 0

        for repo_meta in rotation_ring:
            if len(existing_real_items) >= target_real_issues:
                break

            repo_name = repo_meta.get("full_name")
            if not repo_name:
                continue

            current_cnt = repo_counts[repo_name]
            if current_cnt >= per_repo_cap:
                continue

            needed = min(per_repo_cap - current_cnt, target_real_issues - len(existing_real_items))
            if needed <= 0:
                continue

            # Fetch page of issues
            try:
                state_to_fetch = "open" if pass_round <= 4 else "all"
                page = pass_round
                api_url = f"https://api.github.com/repos/{repo_name}/issues"
                raw_items = github.get(api_url, params={"state": state_to_fetch, "per_page": 20, "page": page})

                if not isinstance(raw_items, list) or not raw_items:
                    continue

                repo_added = 0
                for raw_item in raw_items:
                    if len(existing_real_items) >= target_real_issues:
                        break
                    if repo_counts[repo_name] >= per_repo_cap:
                        break

                    issue_num = raw_item.get("number")
                    if not issue_num:
                        continue

                    # STRICT REAL ISSUE FILTER: Skip pull requests
                    is_pr = "pull_request" in raw_item and raw_item["pull_request"] is not None
                    if is_pr:
                        continue

                    key = (repo_name.lower(), int(issue_num))
                    if key in existing_real_items:
                        continue

                    # Build structured record
                    title = (raw_item.get("title") or "").strip()
                    body = (raw_item.get("body") or "").strip()
                    raw_comment_count = int(raw_item.get("comments", 0))

                    # Fetch comments if available
                    comments, comment_authors, comment_timestamps = [], [], []
                    if raw_comment_count > 0:
                        try:
                            c_url = f"https://api.github.com/repos/{repo_name}/issues/{issue_num}/comments"
                            c_data = github.get(c_url, params={"per_page": 3})
                            if isinstance(c_data, list):
                                for c in c_data[:3]:
                                    c_body = (c.get("body") or "").strip()
                                    if c_body:
                                        comments.append(c_body)
                                        comment_authors.append((c.get("user") or {}).get("login", "unknown"))
                                        comment_timestamps.append(c.get("created_at") or "")
                        except Exception:
                            pass

                    # Labels
                    raw_labels = raw_item.get("labels") or []
                    normalized_labels = []
                    for lbl in raw_labels:
                        if isinstance(lbl, dict):
                            normalized_labels.append({
                                "name": lbl.get("name", ""),
                                "color": lbl.get("color", ""),
                                "description": lbl.get("description") or ""
                            })
                        else:
                            normalized_labels.append({"name": str(lbl), "color": "", "description": ""})

                    assignees = [a.get("login") for a in (raw_item.get("assignees") or []) if isinstance(a, dict) and a.get("login")]

                    # Pipeline Observation Fields
                    pf_res = pre_filter_issue(title=title, body=body, labels=raw_labels)
                    sb_entry = sb_issues_map.get(key)

                    record = {
                        "dataset_id": f"gn_real_{uuid.uuid4().hex[:12]}",
                        "repo_id": repo_meta.get("id"),
                        "repo_name": repo_name,
                        "owner": repo_name.split("/")[0] if "/" in repo_name else "",
                        "repo_url": f"https://github.com/{repo_name}",
                        "issue_number": int(issue_num),
                        "issue_url": raw_item.get("html_url") or f"https://github.com/{repo_name}/issues/{issue_num}",
                        "title": title,
                        "body": body,
                        "labels": normalized_labels,
                        "issue_state": raw_item.get("state", "open"),
                        "created_at": raw_item.get("created_at"),
                        "updated_at": raw_item.get("updated_at"),
                        "closed_at": raw_item.get("closed_at"),
                        "author_login": (raw_item.get("user") or {}).get("login", "unknown"),
                        "comments_count": raw_comment_count,
                        "comments": comments,
                        "comment_authors": comment_authors,
                        "comment_timestamps": comment_timestamps,
                        "repo_language": repo_meta.get("language") or "Unknown",
                        "repo_languages": [repo_meta.get("language")] if repo_meta.get("language") else [],
                        "repo_topics": repo_meta.get("topics") or [],
                        "repo_description": repo_meta.get("description") or "",
                        "repo_stars": repo_meta.get("stars", 0),
                        "repo_forks": repo_meta.get("forks", 0),
                        "repo_open_issues_count": raw_item.get("open_issues_count", 0),
                        "repo_default_branch": repo_meta.get("default_branch") or "main",
                        "assignees": assignees,
                        "assignee_count": len(assignees),
                        "milestone": raw_item.get("milestone", {}).get("title") if isinstance(raw_item.get("milestone"), dict) else None,
                        "milestone_title": raw_item.get("milestone", {}).get("title") if isinstance(raw_item.get("milestone"), dict) else None,
                        "is_pull_request": False,
                        "is_locked": raw_item.get("locked", False),
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                        "discovery_source": "github_rest_api_v3",
                        "discovery_run_id": run_id,
                        "github_api_endpoint": f"https://api.github.com/repos/{repo_name}/issues",
                        "collection_version": "v2.0.0",
                        "existing_prefilter_decision": "PASS" if pf_res.get("pass") else "DROP",
                        "existing_prefilter_reason": pf_res.get("reason"),
                        "existing_publication_status": sb_entry.get("is_published") if sb_entry else "NOT_IN_SUPABASE",
                        "existing_difficulty": sb_entry.get("difficulty_tier") or sb_entry.get("difficulty") if sb_entry else None,
                        "linked_pr_numbers": [],
                        "linked_pr_urls": [],
                        "resolution_pr_count": 0,
                        "has_merged_pr": None,
                        "label": None,
                        "label_source": None,
                        "label_confidence": None
                    }

                    existing_real_items[key] = record
                    repo_counts[repo_name] += 1
                    repo_added += 1
                    added_in_round += 1

                if repo_added > 0:
                    print(f"   ✔ [{repo_meta.get('language', 'Other')}] {repo_name}: +{repo_added} real issues (Repo: {repo_counts[repo_name]}/{per_repo_cap}) -> Total Real Issues: {len(existing_real_items)}/{target_real_issues}")

            except Exception as err:
                print(f"   ⚠️ Error fetching {repo_name}: {err}")
                continue

        if added_in_round == 0:
            print(f"⚠️ No additional real issues discovered in round {pass_round}.")
            break

        pass_round += 1

    elapsed = time.time() - start_time
    total_real = len(existing_real_items)
    print(f"\n🎉 Expansion Finished in {elapsed:.2f}s! Total Real Issues: {total_real}")

    # Export v2 files
    v2_jsonl_path = output_dir / "gitnova_real_issues_v2.jsonl"
    v2_csv_path = output_dir / "gitnova_real_issues_v2.csv"
    v2_manifest_path = output_dir / "collection_manifest_v2.json"
    v2_quality_report_path = output_dir / "quality_report_v2.json"

    # 1. JSONL Export
    with open(v2_jsonl_path, "w", encoding="utf-8") as f:
        for item in existing_real_items.values():
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"💾 Saved {v2_jsonl_path} ({total_real} records)")

    # 2. CSV Export
    fieldnames = [
        "dataset_id", "repo_name", "repo_language", "issue_number", "title",
        "issue_state", "is_pull_request", "author_login", "comments_count",
        "assignee_count", "existing_prefilter_decision", "existing_prefilter_reason",
        "existing_publication_status", "existing_difficulty", "created_at", "issue_url"
    ]
    with open(v2_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in existing_real_items.values():
            row = {k: record.get(k) for k in fieldnames}
            if row.get("title"):
                row["title"] = row["title"].replace("\n", " ").replace("\r", " ")[:150]
            writer.writerow(row)
    print(f"💾 Saved {v2_csv_path}")

    # 3. Quality Metrics
    real_list = list(existing_real_items.values())
    final_repo_counts = Counter(r["repo_name"] for r in real_list)
    final_lang_counts = Counter(r["repo_language"] for r in real_list)
    final_issue_types = Counter(classify_issue_type(r.get("title", ""), r.get("body", ""), r.get("labels", [])) for r in real_list)
    final_body_words = [len((r.get("body") or "").split()) for r in real_list]
    sorted_words = sorted(final_body_words)

    max_repo, max_repo_cnt = final_repo_counts.most_common(1)[0] if final_repo_counts else ("None", 0)
    max_lang, max_lang_cnt = final_lang_counts.most_common(1)[0] if final_lang_counts else ("None", 0)

    quality_v2 = {
        "manifest_version": "2.0.0",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_real_issues": target_real_issues,
        "collected_real_issues": total_real,
        "metrics": {
            "total_real_issues": total_real,
            "unique_repositories": len(final_repo_counts),
            "unique_languages": len(final_lang_counts),
            "average_body_words": round(sum(final_body_words) / total_real, 1) if total_real else 0,
            "median_body_words": sorted_words[total_real // 2] if total_real else 0,
            "short_issues_count": sum(1 for w in final_body_words if w < 20),
            "short_issues_pct": round((sum(1 for w in final_body_words if w < 20) / total_real) * 100, 2) if total_real else 0,
            "long_issues_count": sum(1 for w in final_body_words if w > 500),
            "missing_bodies_count": sum(1 for w in final_body_words if w == 0),
            "missing_titles_count": sum(1 for r in real_list if not (r.get("title") or "").strip()),
            "issues_with_comments_count": sum(1 for r in real_list if (r.get("comments_count") or 0) > 0),
            "issues_with_comments_pct": round((sum(1 for r in real_list if (r.get("comments_count") or 0) > 0) / total_real) * 100, 2) if total_real else 0,
        },
        "concentration": {
            "max_repository": {"name": max_repo, "count": max_repo_cnt, "percentage": round((max_repo_cnt / total_real) * 100, 2)},
            "max_language": {"name": max_lang, "count": max_lang_cnt, "percentage": round((max_lang_cnt / total_real) * 100, 2)},
            "warnings": []
        },
        "distributions": {
            "issue_types": {k: {"count": cnt, "pct": round((cnt / total_real) * 100, 2)} for k, cnt in final_issue_types.most_common()},
            "languages": dict(final_lang_counts.most_common()),
            "top_20_repositories": dict(final_repo_counts.most_common(20))
        },
        "dataset_status": "READY_FOR_LABELING" if total_real >= 500 else "COLLECT_MORE_ISSUES"
    }

    with open(v2_quality_report_path, "w", encoding="utf-8") as f:
        json.dump(quality_v2, f, indent=2)
    print(f"💾 Saved {v2_quality_report_path}")

    # 4. Manifest Export
    manifest_v2 = {
        "manifest_version": "2.0.0",
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_real_issues": total_real,
        "target_real_issues": target_real_issues,
        "per_repo_cap": per_repo_cap,
        "duration_seconds": round(elapsed, 2),
        "dataset_files": {
            "real_issues_jsonl": str(v2_jsonl_path.name),
            "real_issues_csv": str(v2_csv_path.name),
            "raw_v1_jsonl_unmodified": str(raw_v1_path.name),
            "audit_report": "audit_v2/dataset_audit_v2.md",
            "quality_report": str(v2_quality_report_path.name)
        }
    }
    with open(v2_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_v2, f, indent=2)
    print(f"💾 Saved {v2_manifest_path}")

    return quality_v2


if __name__ == "__main__":
    audit_res = perform_phase1_audit(
        raw_jsonl_path=backend_path / "data" / "dataset_collection" / "gitnova_raw_issues_v1.jsonl",
        audit_dir=backend_path / "data" / "dataset_collection" / "audit_v2"
    )
    if audit_res.get("recommendation") == "COLLECT_MORE_ISSUES":
        perform_phase2_expansion(target_real_issues=600, per_repo_cap=15)
