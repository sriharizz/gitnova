"""
GitNova — Issue Discovery Script (uses GitHubClient with authenticated token)
Finds 3 NEW real open issues (1 Python, 1 TypeScript, 1 Rust) that:
  - Are OPEN
  - Have >= 1 label (good first issue / help wanted / bug)
  - Are NOT previously used in GitNova quality gates
  - Have a meaningful body (>= 100 chars)
  - Are NOT assigned to anyone
"""
import os
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.pipeline.github_client import GitHubClient

# Previously used — DO NOT reuse
BANNED_ISSUES = {
    ("pallets/flask", 6123),
    ("pallets/flask", 6093),
    ("pallets/flask", 6065),
    ("pallets/click", 3740),
    ("pallets/click", 2645),
    ("tinygrad/tinygrad", 6043),
    ("encode/starlette", 2341),
    ("colinhacks/zod", 2411),
    ("BurntSushi/ripgrep", 2145),
}

# Candidate repos per language
REPOS_TO_SEARCH = {
    "Python": [
        "psf/requests",
        "pallets/click",
        "httpie/cli",
        "pydantic/pydantic",
        "astral-sh/ruff",
    ],
    "TypeScript": [
        "facebook/docusaurus",
        "sindresorhus/execa",
        "trpc/trpc",
        "withastro/astro",
        "remix-run/remix",
    ],
    "Rust": [
        "sharkdp/bat",
        "clap-rs/clap",
        "serde-rs/serde",
        "tokio-rs/tokio",
        "hyperium/hyper",
    ],
}

GOOD_LABELS = {"good first issue", "help wanted", "bug", "good-first-issue", "E-easy", "D-easy"}
MIN_BODY_LEN = 100


def score_issue(issue: dict) -> float:
    """Score an issue for quality gate suitability."""
    score = 0.0
    body = (issue.get("body") or "")
    labels = [l.get("name", "").lower() for l in (issue.get("labels") or [])]

    if len(body) > 300:
        score += 2.0
    if len(body) > 100:
        score += 1.0
    if any(l in GOOD_LABELS for l in labels):
        score += 3.0
    if not issue.get("assignee"):
        score += 2.0
    if issue.get("comments", 0) >= 1:
        score += 1.0
    if issue.get("comments", 0) >= 3:
        score += 1.0
    return score


def find_best_issue_for_repo(github: GitHubClient, repo: str) -> dict | None:
    """Search for best open beginner issue in a repo."""
    url = f"https://api.github.com/repos/{repo}/issues"
    try:
        issues = github.get(url, params={
            "state": "open",
            "per_page": 20,
            "sort": "updated",
            "direction": "desc"
        })
        if not isinstance(issues, list):
            print(f"  ⚠️  {repo}: unexpected response type")
            return None

        candidates = []
        for issue in issues:
            if issue.get("pull_request"):
                continue  # skip PRs
            if issue.get("assignee") or (issue.get("assignees") and len(issue.get("assignees")) > 0):
                continue  # skip assigned issues
            num = issue.get("number")
            repo_lower = repo.lower()
            # Check ban list (case-insensitive)
            banned = any(
                repo_lower == b[0].lower() and num == b[1]
                for b in BANNED_ISSUES
            )
            if banned:
                continue
            body = issue.get("body") or ""
            if len(body) < MIN_BODY_LEN:
                continue
            score = score_issue(issue)
            candidates.append((score, issue))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_issue = candidates[0]
        return best_issue

    except Exception as e:
        print(f"  ❌ Error fetching {repo}: {e}")
        return None


def main():
    github = GitHubClient()
    print(f"\n{'='*60}")
    print("GitNova — 3-Issue Discovery (Authenticated GitHubClient)")
    print(f"{'='*60}\n")

    selected = {}  # language -> issue dict

    for language, repos in REPOS_TO_SEARCH.items():
        print(f"\n🔍 Searching for {language} issue...")
        for repo in repos:
            if language in selected:
                break
            print(f"  → Checking {repo}...")
            issue = find_best_issue_for_repo(github, repo)
            if issue:
                selected[language] = {
                    "repo": repo,
                    "issue": issue
                }
                labels = [l.get("name") for l in (issue.get("labels") or [])]
                body_preview = (issue.get("body") or "")[:120].replace("\n", " ")
                print(f"  ✅ SELECTED: #{issue['number']} — {issue['title']}")
                print(f"     Labels: {labels}")
                print(f"     Assignee: {issue.get('assignee')}")
                print(f"     Comments: {issue.get('comments', 0)}")
                print(f"     Body preview: {body_preview}...")
            else:
                print(f"  ⛔ No suitable issue in {repo}")

    print(f"\n{'='*60}")
    print("FINAL SELECTION SUMMARY")
    print(f"{'='*60}\n")

    final_issues = []
    for lang in ["Python", "TypeScript", "Rust"]:
        if lang not in selected:
            print(f"❌ FAILED TO FIND {lang} ISSUE — try more repos manually")
            continue
        entry = selected[lang]
        issue = entry["issue"]
        repo = entry["repo"]
        labels = [l.get("name") for l in (issue.get("labels") or [])]
        print(f"[{lang}]")
        print(f"  Repo:   {repo}")
        print(f"  Issue:  #{issue['number']} — {issue['title']}")
        print(f"  URL:    {issue.get('html_url')}")
        print(f"  Labels: {labels}")
        print(f"  State:  {issue.get('state')}")
        print(f"  Assignee: {issue.get('assignee')}")
        print(f"  Comments: {issue.get('comments', 0)}")
        print()
        final_issues.append({
            "language": lang,
            "repo": repo,
            "issue_number": issue["number"],
            "title": issue["title"],
            "url": issue.get("html_url"),
            "labels": labels,
            "state": issue.get("state"),
            "assignee": issue.get("assignee"),
            "comments": issue.get("comments", 0),
            "body_length": len(issue.get("body") or ""),
            "body_preview": (issue.get("body") or "")[:300],
        })

    # Save as JSON for audit plan review
    out_path = Path(__file__).parent / "data" / "three_new_issues_candidates.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_issues, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Candidates saved to: {out_path}")
    print(f"GitHub API requests used: {github.request_count}")
    print(f"GitHub API remaining:     {github.remaining}")


if __name__ == "__main__":
    main()
