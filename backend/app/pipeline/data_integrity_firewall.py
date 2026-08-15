"""
GitNova v4.4.1 — Canonical Ingestion & Data Integrity Firewall Engine

Enforces strict canonical verification against GitHub API before any record
can enter the processing pipeline or be persisted with is_published=True.

Hard Invariants:
  1. Entity is an ISSUE (NOT a Pull Request).
  2. Repository full name and issue number match canonical GitHub object.
  3. Canonical HTML URL matches expected issue URL pattern.
  4. Title matches canonical GitHub issue title.
  5. State must be OPEN for publication eligibility.
  6. Reporter, assignees, labels, and timestamps originate from GitHub.
  7. Fails CLOSED (is_safe_to_publish = False) on any validation failure.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
import json
import urllib.request
import urllib.error
import re
import os


class DataIntegrityFirewall:
    """Production firewall preventing unverified, synthetic, closed, or PR entities from publishing."""

    @staticmethod
    def normalize_title(title: str) -> str:
        """Normalize title string for robust whitespace and quote comparison."""
        if not title:
            return ""
        # Strip outer quotes, normalize whitespace and lowercase
        cleaned = re.sub(r'["\'`]', '', title).strip().lower()
        return " ".join(cleaned.split())

    @classmethod
    def verify_canonical_identity(
        cls,
        repo_full_name: str,
        github_issue_number: int,
        expected_title: Optional[str] = None,
        raw_gh_data: Optional[Dict[str, Any]] = None,
        github_token: Optional[str] = None,
        require_open_state: bool = True
    ) -> Dict[str, Any]:
        """
        Validates an issue candidate against GitHub's authoritative API.
        
        Returns:
            Dict with:
                - data_integrity_status: "VERIFIED" | "INVALID"
                - is_safe_to_publish: bool
                - rejection_reason: Optional[str]
                - canonical_title: str
                - canonical_state: str ("open" | "closed")
                - canonical_url: str
                - is_pull_request: bool
                - reporter_username: str
                - assignees: List[str]
                - labels: List[str]
                - comments_count: int
                - github_updated_at: str
                - last_verified_at: str
                - freshness_status: "VERIFIED" | "STALE" | "NEEDS_REVALIDATION" | "INVALID"
                - canonical_gh_data: Optional[Dict]
        """
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        gh_data = raw_gh_data

        # 1. Fetch live canonical GitHub issue payload if not provided
        if gh_data is None:
            token = github_token or os.getenv("GITHUB_TOKEN")
            headers = {"User-Agent": "GitNova-Data-Integrity-Firewall"}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            api_url = f"https://api.github.com/repos/{repo_full_name}/issues/{github_issue_number}"
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    gh_data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return cls._build_invalid_result(
                    reason=f"GitHub API HTTP {e.code}: {e.reason} for {repo_full_name} #{github_issue_number}",
                    now_iso=now_iso
                )
            except Exception as e:
                return cls._build_invalid_result(
                    reason=f"GitHub API connection error for {repo_full_name} #{github_issue_number}: {str(e)}",
                    now_iso=now_iso
                )

        if not isinstance(gh_data, dict):
            return cls._build_invalid_result(
                reason=f"Invalid payload returned by GitHub for {repo_full_name} #{github_issue_number}",
                now_iso=now_iso
            )

        # 2. Hard Invariant: Check if entity is a Pull Request
        is_pr = (
            ("pull_request" in gh_data) or
            ("/pull/" in gh_data.get("html_url", "")) or
            ("/pulls/" in gh_data.get("url", ""))
        )
        if is_pr:
            return cls._build_invalid_result(
                reason=f"Entity #{github_issue_number} in {repo_full_name} is a Pull Request, not an Issue.",
                now_iso=now_iso,
                gh_data=gh_data,
                is_pr=True
            )

        # 3. Hard Invariant: Issue number match
        resp_number = gh_data.get("number")
        if resp_number is not None and int(resp_number) != int(github_issue_number):
            return cls._build_invalid_result(
                reason=f"Issue number mismatch: requested #{github_issue_number} but GitHub returned #{resp_number}",
                now_iso=now_iso,
                gh_data=gh_data
            )

        # 4. Hard Invariant: Canonical URL structure
        html_url = gh_data.get("html_url", "")
        expected_url_sub = f"github.com/{repo_full_name}/issues/{github_issue_number}".lower()
        if expected_url_sub not in html_url.lower():
            return cls._build_invalid_result(
                reason=f"URL mismatch: canonical URL '{html_url}' does not match expected '{expected_url_sub}'",
                now_iso=now_iso,
                gh_data=gh_data
            )

        canonical_title = (gh_data.get("title") or "").strip()
        canonical_state = gh_data.get("state", "").lower()
        github_updated_at = gh_data.get("updated_at")

        # 5. Check Title consistency if expected_title provided
        if expected_title:
            norm_expected = cls.normalize_title(expected_title)
            norm_canonical = cls.normalize_title(canonical_title)
            if norm_expected and norm_canonical and (norm_expected != norm_canonical):
                # If neither is substring of the other
                if norm_expected not in norm_canonical and norm_canonical not in norm_expected:
                    return cls._build_invalid_result(
                        reason=f"Title mismatch. Stored: '{expected_title}' vs GitHub: '{canonical_title}'",
                        now_iso=now_iso,
                        gh_data=gh_data
                    )

        # 6. Check Open State if required for publication
        if require_open_state and canonical_state != "open":
            return {
                "data_integrity_status": "VERIFIED",
                "is_safe_to_publish": False,
                "rejection_reason": f"Issue #{github_issue_number} in {repo_full_name} is closed on GitHub (state: '{canonical_state}')",
                "canonical_title": canonical_title,
                "canonical_state": canonical_state,
                "canonical_url": html_url,
                "is_pull_request": False,
                "reporter_username": gh_data.get("user", {}).get("login", "unknown") if gh_data.get("user") else "unknown",
                "assignees": [a.get("login") for a in gh_data.get("assignees", []) if a and a.get("login")],
                "labels": [l.get("name") for l in gh_data.get("labels", []) if l and l.get("name")],
                "comments_count": int(gh_data.get("comments") or 0),
                "github_updated_at": github_updated_at,
                "last_verified_at": now_iso,
                "freshness_status": "VERIFIED",
                "canonical_gh_data": gh_data
            }

        # 7. Calculate Freshness Status
        freshness_status = "VERIFIED"
        if github_updated_at:
            try:
                upd_dt = datetime.fromisoformat(github_updated_at.replace("Z", "+00:00"))
                if now_dt - upd_dt > timedelta(days=30):
                    freshness_status = "STALE"
            except Exception:
                freshness_status = "VERIFIED"

        # 8. Complete Canonical Verification Passed
        reporter = gh_data.get("user", {}).get("login", "unknown") if gh_data.get("user") else "unknown"
        assignees = [a.get("login") for a in gh_data.get("assignees", []) if a and a.get("login")]
        labels = [l.get("name") for l in gh_data.get("labels", []) if l and l.get("name")]
        comments_count = int(gh_data.get("comments") or 0)

        return {
            "data_integrity_status": "VERIFIED",
            "is_safe_to_publish": (canonical_state == "open"),
            "rejection_reason": None,
            "canonical_title": canonical_title,
            "canonical_state": canonical_state,
            "canonical_url": html_url,
            "is_pull_request": False,
            "reporter_username": reporter,
            "assignees": assignees,
            "labels": labels,
            "comments_count": comments_count,
            "github_updated_at": github_updated_at,
            "last_verified_at": now_iso,
            "freshness_status": freshness_status,
            "canonical_gh_data": gh_data
        }

    @staticmethod
    def _build_invalid_result(
        reason: str,
        now_iso: str,
        gh_data: Optional[Dict[str, Any]] = None,
        is_pr: bool = False
    ) -> Dict[str, Any]:
        """Helper to build consistent invalid verification result."""
        return {
            "data_integrity_status": "INVALID",
            "is_safe_to_publish": False,
            "rejection_reason": reason,
            "canonical_title": gh_data.get("title") if gh_data else None,
            "canonical_state": gh_data.get("state", "unknown") if gh_data else "unknown",
            "canonical_url": gh_data.get("html_url") if gh_data else None,
            "is_pull_request": is_pr,
            "reporter_username": gh_data.get("user", {}).get("login") if (gh_data and gh_data.get("user")) else None,
            "assignees": [a.get("login") for a in gh_data.get("assignees", []) if a] if gh_data else [],
            "labels": [l.get("name") for l in gh_data.get("labels", []) if l] if gh_data else [],
            "comments_count": int(gh_data.get("comments") or 0) if gh_data else 0,
            "github_updated_at": gh_data.get("updated_at") if gh_data else None,
            "last_verified_at": now_iso,
            "freshness_status": "INVALID",
            "canonical_gh_data": gh_data
        }
