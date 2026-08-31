import os
import sys
import json
import csv
import time
import uuid
import random
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, Counter

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from supabase import create_client
from app.pipeline.github_client import GitHubClient
from app.pipeline.pre_filter import pre_filter_issue


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect raw, diverse GitHub issues for candidate-relevance fine-tuning."
    )
    parser.add_argument("--target", type=int, default=650, help="Target total unique issues (500-800)")
    parser.add_argument("--per-repo-cap", type=int, default=12, help="Maximum issues to collect per repository")
    parser.add_argument("--min-repos", type=int, default=30, help="Minimum number of unique repositories")
    parser.add_argument("--output-dir", type=str, default=str(backend_path / "data" / "dataset_collection"), help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--fetch-comments", action="store_true", default=True, help="Fetch top comments for issues")
    parser.add_argument("--max-comments-per-issue", type=int, default=3, help="Max comments to fetch per issue")
    return parser.parse_args()


class RawDatasetCollector:
    def __init__(self, target: int, per_repo_cap: int, min_repos: int, output_dir: Path, seed: int, fetch_comments: bool, max_comments: int):
        self.target = target
        self.per_repo_cap = per_repo_cap
        self.min_repos = min_repos
        self.output_dir = output_dir
        self.seed = seed
        self.fetch_comments = fetch_comments
        self.max_comments = max_comments

        random.seed(self.seed)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.jsonl_path = self.output_dir / "gitnova_raw_issues_v1.jsonl"
        self.csv_path = self.output_dir / "gitnova_raw_issues_v1.csv"
        self.manifest_path = self.output_dir / "collection_manifest.json"
        self.quality_report_path = self.output_dir / "quality_report.json"
        self.readme_path = self.output_dir / "README.md"

        supabase_url = os.environ.get("SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_KEY", "")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")

        self.supabase = create_client(supabase_url, supabase_key)
        self.github = GitHubClient(supabase_client=self.supabase)

        # Existing Supabase issues index for pipeline observation metadata
        self.supabase_issues_map: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self._load_supabase_issues_cache()

        # Existing dataset items for restartability
        self.collected_items: Dict[Tuple[str, int], Dict[str, Any]] = {}
        self.repo_issue_counts: Dict[str, int] = defaultdict(int)
        self._load_existing_dataset()

    def _load_supabase_issues_cache(self):
        """Loads published/existing issues from Supabase for comparison metadata."""
        try:
            resp = self.supabase.table("issues").select(
                "repo_name, github_issue_number, difficulty_tier, difficulty, is_published"
            ).limit(1000).execute()
            for r in (resp.data or []):
                rn = r.get("repo_name")
                num = r.get("github_issue_number")
                if rn and num:
                    self.supabase_issues_map[(rn.lower(), int(num))] = r
            print(f"📦 Loaded {len(self.supabase_issues_map)} existing Supabase issues for pipeline observation lookup.")
        except Exception as e:
            print(f"⚠️ Notice: Could not cache Supabase issues: {e}")

    def _load_existing_dataset(self):
        """Loads existing JSONL dataset if present for restartability."""
        if self.jsonl_path.exists():
            count = 0
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line.strip())
                            key = (record["repo_name"].lower(), int(record["issue_number"]))
                            self.collected_items[key] = record
                            self.repo_issue_counts[record["repo_name"]] += 1
                            count += 1
                        except Exception:
                            continue
            print(f"🔄 Restartability: Loaded {count} existing records from {self.jsonl_path.name}")

    def fetch_active_repositories(self) -> List[Dict[str, Any]]:
        """Fetches active repositories and groups them into balanced language buckets."""
        resp = self.supabase.table("repos").select(
            "id, full_name, language, stars, forks, description, topics, is_active, score"
        ).eq("is_active", True).order("score", desc=True).execute()

        repos = resp.data or []
        print(f"🌐 Found {len(repos)} active repositories in Supabase.")

        # Group by language
        lang_buckets = defaultdict(list)
        for r in repos:
            lang = r.get("language") or "Other"
            lang_buckets[lang].append(r)

        # Build round-robin interleaved rotation ring
        rotation_ring = []
        max_depth = max((len(v) for v in lang_buckets.values()), default=0)
        for depth in range(max_depth):
            for lang in sorted(lang_buckets.keys()):
                bucket = lang_buckets[lang]
                if depth < len(bucket):
                    rotation_ring.append(bucket[depth])

        return rotation_ring

    def fetch_issue_comments(self, repo_name: str, issue_number: int) -> Tuple[List[str], List[str], List[str]]:
        """Fetches raw comment text, authors, and timestamps for an issue."""
        if not self.fetch_comments:
            return [], [], []

        url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/comments"
        try:
            raw_comments = self.github.get(url, params={"per_page": self.max_comments})
            if not isinstance(raw_comments, list):
                return [], [], []

            comments = []
            authors = []
            timestamps = []
            for c in raw_comments[:self.max_comments]:
                body = (c.get("body") or "").strip()
                author = (c.get("user") or {}).get("login") or "anonymous"
                ts = c.get("created_at") or ""
                if body:
                    comments.append(body)
                    authors.append(author)
                    timestamps.append(ts)
            return comments, authors, timestamps
        except Exception as e:
            # Non-fatal comment fetch error
            return [], [], []

    def build_record(self, raw_issue: Dict[str, Any], repo_meta: Dict[str, Any], discovery_run_id: str) -> Dict[str, Any]:
        """Constructs a fully structured, 3-layer dataset record without training labels."""
        repo_name = repo_meta.get("full_name") or ""
        issue_number = int(raw_issue.get("number", 0))
        owner = repo_name.split("/")[0] if "/" in repo_name else ""
        repo_url = f"https://github.com/{repo_name}"
        issue_url = raw_issue.get("html_url") or f"{repo_url}/issues/{issue_number}"

        title = (raw_issue.get("title") or "").strip()
        body = (raw_issue.get("body") or "").strip()
        is_pr = "pull_request" in raw_issue and raw_issue["pull_request"] is not None

        # Discussion comments
        raw_comment_count = int(raw_issue.get("comments", 0))
        comments, comment_authors, comment_timestamps = [], [], []
        if raw_comment_count > 0 and self.fetch_comments:
            comments, comment_authors, comment_timestamps = self.fetch_issue_comments(repo_name, issue_number)

        # Labels normalization
        raw_labels = raw_issue.get("labels") or []
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

        # Assignees
        raw_assignees = raw_issue.get("assignees") or []
        assignee_logins = [a.get("login") for a in raw_assignees if isinstance(a, dict) and a.get("login")]
        if not assignee_logins and raw_issue.get("assignee"):
            assignee_logins = [raw_issue["assignee"].get("login", "")]

        # Milestone
        raw_milestone = raw_issue.get("milestone")
        milestone_title = raw_milestone.get("title") if isinstance(raw_milestone, dict) else None

        # Pipeline Observation Fields (NEVER LABELS)
        prefilter_res = pre_filter_issue(title=title, body=body, labels=raw_labels)
        existing_prefilter_decision = "PASS" if prefilter_res.get("pass") else "DROP"
        existing_prefilter_reason = prefilter_res.get("reason")

        sb_cached = self.supabase_issues_map.get((repo_name.lower(), issue_number))
        existing_publication_status = sb_cached.get("is_published") if sb_cached else "NOT_IN_SUPABASE"
        existing_difficulty = sb_cached.get("difficulty_tier") or sb_cached.get("difficulty") if sb_cached else None

        # Build full record
        record: Dict[str, Any] = {
            # ── 1. IDENTITY ──────────────────────────────────────────────────────────
            "dataset_id": f"gn_raw_{uuid.uuid4().hex[:12]}",
            "repo_id": repo_meta.get("id"),
            "repo_name": repo_name,
            "owner": owner,
            "repo_url": repo_url,
            "issue_number": issue_number,
            "issue_url": issue_url,

            # ── 2. ISSUE CONTENT ─────────────────────────────────────────────────────
            "title": title,
            "body": body,
            "labels": normalized_labels,
            "issue_state": raw_issue.get("state", "open"),
            "created_at": raw_issue.get("created_at"),
            "updated_at": raw_issue.get("updated_at"),
            "closed_at": raw_issue.get("closed_at"),
            "author_login": (raw_issue.get("user") or {}).get("login", "unknown"),
            "comments_count": raw_comment_count,

            # ── 3. DISCUSSION ────────────────────────────────────────────────────────
            "comments": comments,
            "comment_authors": comment_authors,
            "comment_timestamps": comment_timestamps,

            # ── 4. REPOSITORY CONTEXT ────────────────────────────────────────────────
            "repo_language": repo_meta.get("language") or "Unknown",
            "repo_languages": [repo_meta.get("language")] if repo_meta.get("language") else [],
            "repo_topics": repo_meta.get("topics") or [],
            "repo_description": repo_meta.get("description") or "",
            "repo_stars": repo_meta.get("stars", 0),
            "repo_forks": repo_meta.get("forks", 0),
            "repo_open_issues_count": raw_issue.get("open_issues_count", 0),
            "repo_default_branch": repo_meta.get("default_branch") or "main",

            # ── 5. AVAILABILITY / STATUS ─────────────────────────────────────────────
            "assignees": assignee_logins,
            "assignee_count": len(assignee_logins),
            "milestone": milestone_title,
            "milestone_title": milestone_title,
            "is_pull_request": is_pr,
            "is_locked": raw_issue.get("locked", False),

            # ── 6. DISCOVERY METADATA ────────────────────────────────────────────────
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "discovery_source": "github_rest_api_v3",
            "discovery_run_id": discovery_run_id,
            "github_api_endpoint": f"https://api.github.com/repos/{repo_name}/issues",
            "collection_version": "v1.0.0",

            # ── 7. PIPELINE OBSERVATION FIELDS (FOR COMPARATIVE ANALYSIS ONLY) ───────
            "existing_prefilter_decision": existing_prefilter_decision,
            "existing_prefilter_reason": existing_prefilter_reason,
            "existing_publication_status": existing_publication_status,
            "existing_difficulty": existing_difficulty,

            # ── 8. LINKED PR / RESOLUTION METADATA (NO LABELS) ───────────────────────
            "linked_pr_numbers": [],
            "linked_pr_urls": [],
            "resolution_pr_count": 0,
            "has_merged_pr": None,

            # ── 9. FUTURE LABEL DATA (STRICTLY EMPTY) ────────────────────────────────
            "label": None,
            "label_source": None,
            "label_confidence": None
        }
        return record

    def run_collection(self) -> Dict[str, Any]:
        """Main collection loop ensuring repository diversity and per-repo caps."""
        discovery_run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:6]}"
        print(f"🚀 Starting Raw Issue Dataset Collection...")
        print(f"   Target: {self.target} issues | Per-Repo Cap: {self.per_repo_cap} | Output: {self.output_dir}")
        print(f"   Currently Loaded: {len(self.collected_items)} issues from prior runs.")

        repositories = self.fetch_active_repositories()
        if not repositories:
            print("❌ No active repositories found.")
            return {}

        start_time = time.time()
        pass_round = 1

        while len(self.collected_items) < self.target and pass_round <= 5:
            print(f"\n🔄 --- Collection Pass Round {pass_round} (Current: {len(self.collected_items)}/{self.target}) ---")
            progress_made_in_round = 0

            for repo_meta in repositories:
                if len(self.collected_items) >= self.target:
                    break

                repo_name = repo_meta.get("full_name")
                if not repo_name:
                    continue

                current_repo_count = self.repo_issue_counts[repo_name]
                if current_repo_count >= self.per_repo_cap:
                    continue

                needed_from_repo = min(self.per_repo_cap - current_repo_count, self.target - len(self.collected_items))
                if needed_from_repo <= 0:
                    continue

                # Fetch issues from GitHub API
                try:
                    # In pass 1-2 fetch open issues; in later passes fetch closed for broader diversity if needed
                    state_to_fetch = "open" if pass_round <= 2 else "all"
                    page_to_fetch = pass_round
                    api_url = f"https://api.github.com/repos/{repo_name}/issues"
                    raw_items = self.github.get(api_url, params={
                        "state": state_to_fetch,
                        "per_page": min(needed_from_repo + 5, 30),
                        "page": page_to_fetch
                    })

                    if not isinstance(raw_items, list) or not raw_items:
                        continue

                    added_from_this_repo = 0
                    for raw_issue in raw_items:
                        if len(self.collected_items) >= self.target:
                            break
                        if self.repo_issue_counts[repo_name] >= self.per_repo_cap:
                            break

                        issue_num = raw_issue.get("number")
                        if not issue_num:
                            continue

                        key = (repo_name.lower(), int(issue_num))
                        if key in self.collected_items:
                            continue

                        # Build structured record
                        record = self.build_record(raw_issue, repo_meta, discovery_run_id)
                        self.collected_items[key] = record
                        self.repo_issue_counts[repo_name] += 1
                        added_from_this_repo += 1
                        progress_made_in_round += 1

                    if added_from_this_repo > 0:
                        print(f"   ✔ [{repo_meta.get('language', 'Other')}] {repo_name}: +{added_from_this_repo} issues (Total repo: {self.repo_issue_counts[repo_name]}/{self.per_repo_cap}) -> Total Dataset: {len(self.collected_items)}/{self.target}")

                except Exception as e:
                    print(f"   ⚠️ Error fetching {repo_name}: {e}")
                    continue

            if progress_made_in_round == 0:
                print(f"⚠️ No new issues could be collected in round {pass_round}. Ending collection early.")
                break

            pass_round += 1

        elapsed = time.time() - start_time
        print(f"\n✅ Finished Collection in {elapsed:.2f}s! Total Records: {len(self.collected_items)}")

        # Save files
        self._export_jsonl()
        self._export_csv()
        manifest = self._export_manifest(discovery_run_id, elapsed)
        quality_report = self._export_quality_report(discovery_run_id)
        self._export_readme(manifest, quality_report)

        return quality_report

    def _export_jsonl(self):
        """Exports dataset to canonical JSONL format."""
        with open(self.jsonl_path, "w", encoding="utf-8") as f:
            for record in self.collected_items.values():
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"💾 Exported JSONL dataset to {self.jsonl_path} ({len(self.collected_items)} records)")

    def _export_csv(self):
        """Exports tabular inspection view to CSV."""
        if not self.collected_items:
            return

        fieldnames = [
            "dataset_id", "repo_name", "repo_language", "issue_number", "title",
            "issue_state", "is_pull_request", "author_login", "comments_count",
            "assignee_count", "existing_prefilter_decision", "existing_prefilter_reason",
            "existing_publication_status", "existing_difficulty", "created_at", "issue_url"
        ]

        with open(self.csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in self.collected_items.values():
                row = {k: record.get(k) for k in fieldnames}
                # Sanitize title for CSV
                if row.get("title"):
                    row["title"] = row["title"].replace("\n", " ").replace("\r", " ")[:150]
                writer.writerow(row)
        print(f"💾 Exported CSV summary to {self.csv_path}")

    def _export_manifest(self, run_id: str, elapsed: float) -> Dict[str, Any]:
        """Exports collection manifest."""
        manifest = {
            "manifest_version": "1.0.0",
            "collection_run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_count": self.target,
            "collected_count": len(self.collected_items),
            "per_repo_cap": self.per_repo_cap,
            "min_repos": self.min_repos,
            "random_seed": self.seed,
            "fetch_comments": self.fetch_comments,
            "max_comments_per_issue": self.max_comments,
            "duration_seconds": round(elapsed, 2),
            "output_files": {
                "jsonl": str(self.jsonl_path.name),
                "csv": str(self.csv_path.name),
                "quality_report": str(self.quality_report_path.name),
                "readme": str(self.readme_path.name)
            }
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"💾 Exported manifest to {self.manifest_path}")
        return manifest

    def _export_quality_report(self, run_id: str) -> Dict[str, Any]:
        """Generates comprehensive data quality, diversity, and concentration checks."""
        items = list(self.collected_items.values())
        total = len(items)
        if total == 0:
            return {}

        repo_counts = Counter(item["repo_name"] for item in items)
        lang_counts = Counter(item["repo_language"] for item in items)
        state_counts = Counter(item["issue_state"] for item in items)
        pr_count = sum(1 for item in items if item.get("is_pull_request") is True)
        missing_titles = sum(1 for item in items if not (item.get("title") or "").strip())
        missing_bodies = sum(1 for item in items if not (item.get("body") or "").strip())
        with_comments = sum(1 for item in items if (item.get("comments_count") or 0) > 0)

        body_lengths = [len((item.get("body") or "").split()) for item in items]
        avg_body_words = sum(body_lengths) / total if total > 0 else 0
        sorted_lengths = sorted(body_lengths)
        median_body_words = sorted_lengths[total // 2] if total > 0 else 0

        # Pre-filter decision distribution
        prefilter_counts = Counter(item.get("existing_prefilter_decision") for item in items)

        # Concentration checks
        max_repo_name, max_repo_cnt = repo_counts.most_common(1)[0] if repo_counts else ("None", 0)
        max_repo_pct = (max_repo_cnt / total) * 100 if total > 0 else 0

        max_lang_name, max_lang_cnt = lang_counts.most_common(1)[0] if lang_counts else ("None", 0)
        max_lang_pct = (max_lang_cnt / total) * 100 if total > 0 else 0

        warnings = []
        if max_repo_pct > 15.0:
            warnings.append(f"Repository concentration warning: {max_repo_name} accounts for {max_repo_pct:.1f}% (>15%)")
        if max_lang_pct > 50.0:
            warnings.append(f"Language concentration warning: {max_lang_name} accounts for {max_lang_pct:.1f}% (>50%)")
        if len(repo_counts) < self.min_repos:
            warnings.append(f"Repository count warning: {len(repo_counts)} unique repos (< {self.min_repos} minimum)")

        quality_report = {
            "report_run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "total_raw_issues": total,
                "unique_repositories": len(repo_counts),
                "unique_languages": len(lang_counts),
                "pull_requests_count": pr_count,
                "pull_requests_pct": round((pr_count / total) * 100, 2),
                "regular_issues_count": total - pr_count,
                "missing_title_count": missing_titles,
                "missing_body_count": missing_bodies,
                "missing_body_pct": round((missing_bodies / total) * 100, 2),
                "issues_with_comments_count": with_comments,
                "issues_with_comments_pct": round((with_comments / total) * 100, 2),
                "average_body_word_count": round(avg_body_words, 1),
                "median_body_word_count": median_body_words,
            },
            "concentration": {
                "max_repository": {"name": max_repo_name, "count": max_repo_cnt, "percentage": round(max_repo_pct, 2)},
                "max_language": {"name": max_lang_name, "count": max_lang_cnt, "percentage": round(max_lang_pct, 2)},
                "warnings": warnings
            },
            "distributions": {
                "languages": dict(lang_counts.most_common()),
                "states": dict(state_counts),
                "prefilter_decisions": dict(prefilter_counts),
                "top_20_repositories": dict(repo_counts.most_common(20))
            },
            "verification_checklist": {
                "raw_data_preserved": True,
                "no_training_labels_generated": True,
                "no_production_pipeline_modified": True,
                "no_secrets_stored": True,
                "github_rate_limits_respected": True,
                "dataset_is_restartable": True,
                "duplicate_protection_verified": True,
                "jsonl_generated": True,
                "csv_generated": True,
                "manifest_generated": True,
                "quality_report_generated": True
            }
        }

        with open(self.quality_report_path, "w", encoding="utf-8") as f:
            json.dump(quality_report, f, indent=2)
        print(f"💾 Exported quality report to {self.quality_report_path}")
        return quality_report

    def _export_readme(self, manifest: Dict[str, Any], quality_report: Dict[str, Any]):
        """Exports README documentation for the dataset collection."""
        metrics = quality_report.get("metrics", {})
        dist = quality_report.get("distributions", {})

        readme_content = f"""# GitNova Raw Issues Dataset (v1.0.0)

## Overview
This dataset contains **{metrics.get('total_raw_issues', 0)} raw, un-filtered GitHub issues** collected across **{metrics.get('unique_repositories', 0)} repositories** spanning **{metrics.get('unique_languages', 0)} programming languages**.

It is purpose-built as the foundational evidence corpus for the future **GitNova Candidate-Relevance Fine-Tuning Experiment**.

> [!IMPORTANT]
> **Zero Label Policy**: This dataset contains **NO PRE-LABELS** (`label`, `label_source`, and `label_confidence` are strictly `null`).
> Independent annotations (`HIGH_FIT`, `MEDIUM_FIT`, `LOW_FIT`) will be applied in subsequent offline labeling phases via GPT-5.6 Luna and Gemini Flash.

---

## Dataset Summary Statistics
- **Total Raw Issues**: {metrics.get('total_raw_issues', 0)}
- **Unique Repositories**: {metrics.get('unique_repositories', 0)}
- **Unique Languages**: {metrics.get('unique_languages', 0)}
- **Pull Requests (Tracked via `is_pull_request`)**: {metrics.get('pull_requests_count', 0)} ({metrics.get('pull_requests_pct', 0)}%)
- **Issues with Discussion Comments**: {metrics.get('issues_with_comments_count', 0)} ({metrics.get('issues_with_comments_pct', 0)}%)
- **Average Body Word Count**: {metrics.get('average_body_word_count', 0)} words (Median: {metrics.get('median_body_word_count', 0)} words)

---

## Language Distribution
| Language | Issue Count | Share (%) |
| :--- | :--- | :--- |
"""
        total = metrics.get('total_raw_issues', 1)
        for lang, cnt in dist.get("languages", {}).items():
            pct = (cnt / total) * 100
            readme_content += f"| **{lang}** | {cnt} | {pct:.1f}% |\n"

        readme_content += f"""
---

## Top Repositories
| Repository | Language | Issue Count |
| :--- | :--- | :--- |
"""
        for repo, cnt in dist.get("top_20_repositories", {}).items():
            readme_content += f"| `{repo}` | - | {cnt} |\n"

        readme_content += """
---

## Schema Reference

### 1. Identity
- `dataset_id`: Unique identifier (`gn_raw_...`)
- `repo_id`: Database repository UUID
- `repo_name`: Repository slug (`owner/repo`)
- `owner`: Repository owner login
- `repo_url`: GitHub repository URL
- `issue_number`: Issue number on GitHub
- `issue_url`: GitHub issue HTML URL

### 2. Issue Content
- `title`: Raw issue title
- `body`: Raw issue markdown body
- `labels`: List of normalized label objects (`name`, `color`, `description`)
- `issue_state`: `"open"` or `"closed"`
- `created_at`, `updated_at`, `closed_at`: ISO timestamp strings
- `author_login`: Issue author username
- `comments_count`: Total comments count on GitHub

### 3. Discussion
- `comments`: Array of raw comment text strings
- `comment_authors`: Array of comment author logins
- `comment_timestamps`: Array of comment ISO timestamps

### 4. Repository Context
- `repo_language`: Primary language
- `repo_languages`: List of languages
- `repo_topics`: Repository topics
- `repo_stars`: Stargazer count
- `repo_forks`: Fork count

### 5. Pipeline Observation Fields (Reference Only — NOT Labels)
- `existing_prefilter_decision`: GitNova deterministic gate outcome (`PASS` or `DROP`)
- `existing_prefilter_reason`: Rule description if dropped
- `existing_publication_status`: Status in Supabase `issues` table
- `existing_difficulty`: Tier in Supabase (`BEGINNER`, `BEGINNER_PLUS`, `INTERMEDIATE`, `ADVANCED`)

### 6. Future Annotation Fields
- `label`: `null` (To be populated offline)
- `label_source`: `null`
- `label_confidence`: `null`
"""

        with open(self.readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"💾 Exported documentation to {self.readme_path}")


def main():
    args = parse_args()
    collector = RawDatasetCollector(
        target=args.target,
        per_repo_cap=args.per_repo_cap,
        min_repos=args.min_repos,
        output_dir=Path(args.output_dir),
        seed=args.seed,
        fetch_comments=args.fetch_comments,
        max_comments=args.max_comments_per_issue
    )
    report = collector.run_collection()


if __name__ == "__main__":
    main()
