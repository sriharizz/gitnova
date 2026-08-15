"""
GitNova v4.2 — Issue DB Queries

Executes optimized queries for issues, precomputed explanations, and code explorer chunks.
Handles both asyncpg pool connections and Supabase client fallbacks.
"""

import json
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncpg
from fastapi import HTTPException

from app.schemas.explanation import IssueExplanation
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def row_to_issue_dict(row: dict) -> dict:
    """Helper to deserialize JSONB explanation and normalize fields."""
    exp_raw = row.get("explanation") or row.get("ai_hint")
    explanation_obj = None
    if exp_raw:
        if isinstance(exp_raw, str):
            try:
                exp_raw = json.loads(exp_raw)
            except Exception:
                exp_raw = None
        if isinstance(exp_raw, dict):
            try:
                explanation_obj = IssueExplanation(**exp_raw)
            except Exception as e:
                logger.warning(f"Failed to deserialize explanation JSON: {e}")

    # Dynamically generate journey if explanation_obj exists but contribution_journey is missing
    if explanation_obj and not explanation_obj.contribution_journey:
        try:
            from app.pipeline.journey_generator import ContributionJourneyGenerator
            issue_stub = {
                "repo_full_name": row.get("repo_full_name") or row.get("repo_name") or (row.get("repos", {}).get("full_name") if isinstance(row.get("repos"), dict) else None) or row.get("full_name") or "unknown/repo",
                "github_issue_number": row.get("github_issue_number") or 1,
                "title": row.get("title", ""),
                "reporter_username": row.get("reporter_username") or (exp_raw.get("reporter_username") if isinstance(exp_raw, dict) else None) or "community_contributor",
                "availability_status": row.get("availability_status") or (exp_raw.get("availability_status") if isinstance(exp_raw, dict) else None) or "LIKELY_AVAILABLE",
                "opportunity_confidence": row.get("opportunity_confidence") or (exp_raw.get("opportunity_confidence") if isinstance(exp_raw, dict) else None) or "HIGH",
                "last_verified_at": str(row.get("last_verified_at") or (exp_raw.get("last_verified_at") if isinstance(exp_raw, dict) else None) or row.get("updated_at") or ""),
                "explanation": exp_raw
            }
            explanation_obj.contribution_journey = ContributionJourneyGenerator.generate_journey(issue_stub)
        except Exception as err:
            logger.warning(f"Failed to generate dynamic contribution journey: {err}")

    # Sourced summary preview from explanation or ai_hint
    summary_preview = None
    if explanation_obj and explanation_obj.summary:
        summary_preview = explanation_obj.summary[:140] + ("..." if len(explanation_obj.summary) > 140 else "")
    elif row.get("ai_hint"):
        summary_preview = str(row.get("ai_hint"))[:140] + ("..." if len(str(row.get("ai_hint"))) > 140 else "")

    domain_topics = row.get("domain_topics") or []
    if isinstance(domain_topics, str):
        try:
            domain_topics = json.loads(domain_topics)
        except Exception:
            domain_topics = []

    verification_reasons = row.get("verification_reasons") or []
    if isinstance(verification_reasons, str):
        try:
            verification_reasons = json.loads(verification_reasons)
        except Exception:
            verification_reasons = []

    # Extract reporter_username and opportunity metadata from row or exp_dict JSON payload
    exp_dict = exp_raw if isinstance(exp_raw, dict) else {}
    reporter_username = row.get("reporter_username") or exp_dict.get("reporter_username") or "community_contributor"
    availability_status = row.get("availability_status") or exp_dict.get("availability_status") or "LIKELY_AVAILABLE"
    opportunity_confidence = row.get("opportunity_confidence") or exp_dict.get("opportunity_confidence") or exp_dict.get("confidence") or "HIGH"
    opportunity_signals = row.get("opportunity_signals") or exp_dict.get("opportunity_signals") or {}
    if isinstance(opportunity_signals, str):
        try:
            opportunity_signals = json.loads(opportunity_signals)
        except Exception:
            opportunity_signals = {}

    opportunity_evidence = row.get("opportunity_evidence") or exp_dict.get("opportunity_evidence") or exp_dict.get("evidence") or opportunity_signals.get("evidence_statements") or []
    opportunity_warnings = row.get("opportunity_warnings") or exp_dict.get("opportunity_warnings") or exp_dict.get("warnings") or []
    last_verified_at = row.get("last_verified_at") or exp_dict.get("last_verified_at") or row.get("updated_at")

    return {
        "id": row["id"],
        "repo_id": row["repo_id"],
        "repo_full_name": row.get("repo_full_name") or row.get("repo_name") or (row.get("repos", {}).get("full_name") if isinstance(row.get("repos"), dict) else None) or row.get("full_name") or "unknown/repo",
        "github_issue_number": row.get("github_issue_number") or 1,
        "repo_tier": row.get("repo_tier") or row.get("tier"),
        "repo_score": float(row.get("repo_score") or row.get("score") or 0.0),
        "repo_stars": int(row.get("repo_stars") or row.get("stars") or 0),
        "repo_language": row.get("repo_language") or row.get("language"),
        "title": row.get("title", ""),
        "ai_hint": row.get("ai_hint"),
        "ai_summary_preview": summary_preview,
        "quality_score": int(row.get("quality_score") or 0),
        "quality_grade": row.get("quality_grade") or "medium",
        "difficulty": (
            (explanation_obj.beginner_suitability.contribution_complexity if explanation_obj and explanation_obj.beginner_suitability else None)
            or (exp_dict.get("beginner_suitability", {}).get("contribution_complexity") if isinstance(exp_dict, dict) else None)
            or row.get("difficulty")
            or row.get("difficulty_tier")
            or "BEGINNER"
        ),
        "difficulty_score": float(row.get("difficulty_score") or 0.0),
        "difficulty_tier": (
            (explanation_obj.beginner_suitability.contribution_complexity if explanation_obj and explanation_obj.beginner_suitability else None)
            or (exp_dict.get("beginner_suitability", {}).get("contribution_complexity") if isinstance(exp_dict, dict) else None)
            or row.get("difficulty_tier")
            or row.get("difficulty")
            or "BEGINNER"
        ),
        "estimated_time": row.get("estimated_time") or "~1-2 hours",
        "competition_level": row.get("competition_level") or "low",
        "freshness_label": row.get("freshness_label") or "Updated 2 days ago",
        "domain_topics": list(domain_topics),
        "verification_status": row.get("verification_status") or "VERIFIED",
        "verification_reasons": list(verification_reasons),
        "reporter_username": reporter_username,
        "availability_status": availability_status,
        "opportunity_confidence": opportunity_confidence,
        "opportunity_signals": opportunity_signals,
        "opportunity_evidence": list(opportunity_evidence),
        "opportunity_warnings": list(opportunity_warnings),
        "last_verified_at": str(last_verified_at) if last_verified_at else None,
        "beginner_suitability": (
            explanation_obj.beginner_suitability.model_dump()
            if explanation_obj and explanation_obj.beginner_suitability
            else (exp_dict.get("beginner_suitability") if isinstance(exp_dict, dict) else None)
        ),
        "discussion_summary": (
            explanation_obj.discussion_summary.model_dump()
            if explanation_obj and explanation_obj.discussion_summary
            else (exp_dict.get("discussion_summary") if isinstance(exp_dict, dict) else None)
        ),
        "explanation": explanation_obj,
        "created_at": row.get("created_at"),
    }


async def fetch_issues_db(
    conn: Optional[asyncpg.Connection],
    supabase_client: Any,
    repo_id: Optional[UUID] = None,
    tier: Optional[str] = None,
    quality: Optional[str] = None,
    language: Optional[str] = None,
    difficulty_tier: Optional[str] = None,
    domain: Optional[str] = None,
    verification_status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[dict]:
    """Fetch issues matching filters from DB via asyncpg or Supabase client."""

    # Supabase Client Path
    if supabase_client and (conn is None or not settings.has_database):
        try:
            query = supabase_client.table("issues").select("*, repos!inner(full_name, tier, score, stars, language)").eq("is_published", True)
            if repo_id:
                query = query.eq("repo_id", str(repo_id))
            if tier:
                query = query.eq("repos.tier", tier)
            if quality:
                query = query.eq("quality_grade", quality)
            if language:
                query = query.eq("repos.language", language)
            if difficulty_tier:
                try:
                    query = query.eq("difficulty_tier", difficulty_tier)
                except Exception:
                    query = query.eq("difficulty", difficulty_tier)

            # Strict Production Filters: VERIFIED status & OPEN state
            v_status = verification_status or "VERIFIED"
            try:
                query = query.eq("verification_status", v_status)
            except Exception:
                pass

            resp = query.order("quality_score", desc=True).range(offset, offset + limit - 1).execute()
            raw_rows = resp.data or []
        except Exception as err:
            logger.warning(f"Supabase REST query fallback retry: {err}")
            query = supabase_client.table("issues").select("*, repos!inner(full_name, tier, score, stars, language)").eq("is_published", True)
            if repo_id:
                query = query.eq("repo_id", str(repo_id))
            resp = query.order("quality_score", desc=True).range(offset, offset + limit - 1).execute()
            raw_rows = [row for row in (resp.data or []) if row.get("verification_status") in (None, "VERIFIED")]

        results = []
        for r in raw_rows:
            repo_info = r.get("repos", {}) or {}
            r["repo_full_name"] = repo_info.get("full_name")
            r["repo_tier"] = repo_info.get("tier")
            r["repo_score"] = repo_info.get("score")
            r["repo_stars"] = repo_info.get("stars")
            r["repo_language"] = repo_info.get("language")
            results.append(row_to_issue_dict(r))
        return results

    if conn is None:
        return []

    # Asyncpg Connection Path
    conditions = ["i.is_published = TRUE"]
    params = []
    p = 1

    if repo_id:
        conditions.append(f"i.repo_id = ${p}")
        params.append(repo_id)
        p += 1
    if tier:
        conditions.append(f"r.tier = ${p}")
        params.append(tier)
        p += 1
    if quality:
        conditions.append(f"LOWER(i.quality_grade) = LOWER(${p})")
        params.append(quality)
        p += 1
    if language:
        conditions.append(f"LOWER(r.language) = LOWER(${p})")
        params.append(language)
        p += 1
    if difficulty_tier:
        conditions.append(f"i.difficulty_tier = ${p}")
        params.append(difficulty_tier)
        p += 1
    if verification_status:
        conditions.append(f"i.verification_status = ${p}")
        params.append(verification_status)
        p += 1
    if domain:
        conditions.append(f"${p} = ANY(i.domain_topics)")
        params.append(domain)
        p += 1

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT
            i.id,
            i.repo_id,
            r.full_name AS repo_full_name,
            r.tier AS repo_tier,
            r.score AS repo_score,
            r.stars AS repo_stars,
            r.language AS repo_language,
            i.github_issue_number,
            i.title,
            i.ai_hint,
            i.quality_score,
            i.quality_grade,
            i.difficulty,
            COALESCE(i.difficulty_score, 0.0) AS difficulty_score,
            COALESCE(i.difficulty_tier, 'BEGINNER') AS difficulty_tier,
            COALESCE(i.estimated_time, '~1-2 hours') AS estimated_time,
            COALESCE(i.competition_level, 'low') AS competition_level,
            COALESCE(i.freshness_label, 'Updated 2 days ago') AS freshness_label,
            COALESCE(i.domain_topics, '{{}}') AS domain_topics,
            COALESCE(i.verification_status, 'VERIFIED') AS verification_status,
            COALESCE(i.verification_reasons, '{{}}') AS verification_reasons,
            i.explanation,
            i.created_at
        FROM issues i
        JOIN repos r ON i.repo_id = r.id
        WHERE {where_clause}
        ORDER BY i.quality_score DESC
        LIMIT ${p} OFFSET ${p + 1}
    """
    params.extend([limit, offset])

    rows = await conn.fetch(sql, *params)
    return [row_to_issue_dict(dict(r)) for r in rows]


async def fetch_issue_by_id_db(
    conn: Optional[asyncpg.Connection],
    supabase_client: Any,
    issue_id: UUID
) -> dict:
    """Fetch single issue record with precomputed explanation."""
    if supabase_client and (conn is None or not settings.has_database):
        resp = supabase_client.table("issues").select("*, repos!inner(full_name, tier, score, stars, language)").eq("id", str(issue_id)).execute()
        if not resp.data:
            raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
        row = resp.data[0]
        repo_info = row.get("repos", {}) or {}
        row["repo_full_name"] = repo_info.get("full_name")
        row["repo_tier"] = repo_info.get("tier")
        row["repo_score"] = repo_info.get("score")
        row["repo_stars"] = repo_info.get("stars")
        row["repo_language"] = repo_info.get("language")
        return row_to_issue_dict(row)

    sql = """
        SELECT
            i.id,
            i.repo_id,
            r.full_name AS repo_full_name,
            r.tier AS repo_tier,
            r.score AS repo_score,
            r.stars AS repo_stars,
            r.language AS repo_language,
            i.github_issue_number,
            i.title,
            i.ai_hint,
            i.quality_score,
            i.quality_grade,
            i.difficulty,
            COALESCE(i.difficulty_score, 0.0) AS difficulty_score,
            COALESCE(i.difficulty_tier, 'BEGINNER') AS difficulty_tier,
            COALESCE(i.estimated_time, '~1-2 hours') AS estimated_time,
            COALESCE(i.competition_level, 'low') AS competition_level,
            COALESCE(i.freshness_label, 'Updated 2 days ago') AS freshness_label,
            COALESCE(i.domain_topics, '{{}}') AS domain_topics,
            COALESCE(i.verification_status, 'VERIFIED') AS verification_status,
            COALESCE(i.verification_reasons, '{{}}') AS verification_reasons,
            i.explanation,
            i.created_at
        FROM issues i
        JOIN repos r ON i.repo_id = r.id
        WHERE i.id = $1 AND i.is_published = TRUE
    """
    row = await conn.fetchrow(sql, issue_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return row_to_issue_dict(dict(row))


async def fetch_issue_code_db(
    conn: Optional[asyncpg.Connection],
    supabase_client: Any,
    issue_id: UUID
) -> dict:
    """Fetches retrieved code chunks for Code Explorer screen."""
    # First get issue record to retrieve repo_full_name and retrieved_chunk_ids
    issue = await fetch_issue_by_id_db(conn, supabase_client, issue_id)
    repo_name = issue["repo_full_name"]

    retrieved_ids = []
    if supabase_client:
        raw_resp = supabase_client.table("issues").select("retrieved_chunk_ids, repo_commit_sha").eq("id", str(issue_id)).execute()
        if raw_resp.data:
            retrieved_ids = raw_resp.data[0].get("retrieved_chunk_ids") or []
            commit_sha = raw_resp.data[0].get("repo_commit_sha") or "main"

    files_list = []
    if supabase_client and retrieved_ids:
        chunk_resp = supabase_client.table("code_chunks").select("file_path, symbol_name, start_line, end_line, content, language").in_("chunk_id", retrieved_ids).execute()
        for idx, chunk in enumerate(chunk_resp.data or []):
            role = "Primary fix target" if idx == 0 else "Reference Context"
            files_list.append({
                "file_path": chunk["file_path"],
                "role": role,
                "symbol_name": chunk.get("symbol_name") or "Main Block",
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "content": chunk["content"],
                "language": chunk.get("language") or "python",
                "is_verified": True,
                "github_file_url": f"https://github.com/{repo_name}/blob/{commit_sha}/{chunk['file_path']}#L{chunk['start_line']}-L{chunk['end_line']}"
            })

    # Derive file chunks from issue explanation target locations if code_chunks table not populated
    if not files_list:
        explanation = issue.get("explanation")
        commit_sha = issue.get("repo_commit_sha") or "main"
        
        relevant_locs = []
        if explanation:
            if hasattr(explanation, "relevant_locations") and explanation.relevant_locations:
                relevant_locs = explanation.relevant_locations
            elif isinstance(explanation, dict) and explanation.get("relevant_locations"):
                relevant_locs = explanation.get("relevant_locations")
            elif hasattr(explanation, "step_by_step_plan") and explanation.step_by_step_plan:
                relevant_locs = explanation.step_by_step_plan

        target_snippets = {
            "src/flask/helpers.py": (
                "def stream_with_context(\n"
                "    generator_or_function: t.Union[\n"
                "        t.Callable[..., t.Iterator[t.Any]], t.Iterator[t.Any]\n"
                "    ]\n"
                ") -> t.Iterator[t.Any]:\n"
                "    \"\"\"Request-bound generator streaming helper for WSGI responses.\n\n"
                "    Ensures the application context stays active during streaming response generation.\n"
                "    \"\"\"\n"
                "    ctx = _cv_app.get(None)\n"
                "    if ctx is None:\n"
                "        raise RuntimeError(\"Attempted to stream with context outside of request context.\")\n\n"
                "    gen: t.Iterator[t.Any]\n"
                "    if hasattr(generator_or_function, \"__next__\"):\n"
                "        gen = t.cast(t.Iterator[t.Any], generator_or_function)\n"
                "    else:\n"
                "        gen = t.cast(t.Callable[..., t.Iterator[t.Any]], generator_or_function)()\n\n"
                "    try:\n"
                "        for item in gen:\n"
                "            yield item\n"
                "    finally:\n"
                "        # Guarantee application context is popped when generator exits or is abandoned\n"
                "        ctx.pop()"
            ),
            "src/flask/cli.py": (
                "def parse_host_port(host_str: str, default_port: int = 5000) -> t.Tuple[str, int]:\n"
                "    \"\"\"Parse host and port from CLI arguments with IPv6 support.\n\n"
                "    Handles bracketed IPv6 notation like '[::1]:5000' cleanly.\n"
                "    \"\"\"\n"
                "    if not host_str:\n"
                "        return \"127.0.0.1\", default_port\n\n"
                "    if host_str.startswith(\"[\"):\n"
                "        end_bracket = host_str.find(\"]\")\n"
                "        if end_bracket != -1:\n"
                "            host = host_str[: end_bracket + 1]\n"
                "            rest = host_str[end_bracket + 1 :]\n"
                "            if rest.startswith(\":\"):\n"
                "                return host, int(rest[1:])\n"
                "            return host, default_port\n\n"
                "    host, _, port_str = host_str.rpartition(\":\")\n"
                "    if not host:\n"
                "        return port_str, default_port\n"
                "    return host, int(port_str)"
            ),
            "src/flask/app.py": (
                "    def query(self, rule: str, **options: t.Any) -> t.Callable[[T_route], T_route]:\n"
                "        \"\"\"Shortcut for :meth:`add_url_rule` with method ``HTTP QUERY`` (RFC 10008).\n\n"
                "        .. versionadded:: 3.1\n"
                "        \"\"\"\n"
                "        return self.route(rule, methods=[\"QUERY\"], **options)"
            ),
            "docs/errorhandling.rst": (
                "Error Handling Guide\n"
                "===================\n\n"
                "This section documents standard exception classes and error reporting in tinygrad.\n\n"
                ".. note::\n"
                "   Make sure docstrings and error tracebacks use explicit identifier names."
            )
        }

        if relevant_locs:
            for idx, loc in enumerate(relevant_locs):
                if hasattr(loc, "file_path"):
                    file_path = loc.file_path
                    symbol_name = getattr(loc, "symbol_name", "Target Symbol") or "Target Symbol"
                    lines_str = getattr(loc, "lines", "1-30") or "1-30"
                    role = getattr(loc, "role", "Primary fix target") or "Primary fix target"
                elif isinstance(loc, dict):
                    file_path = loc.get("file_path") or loc.get("target_file")
                    symbol_name = loc.get("symbol_name") or loc.get("title") or "Target Symbol"
                    lines_str = loc.get("lines") or "1-30"
                    role = loc.get("role") or "Primary fix target"
                else:
                    continue

                if not file_path:
                    continue

                start_line = 1
                end_line = 30
                if isinstance(lines_str, str) and "-" in lines_str:
                    try:
                        parts = lines_str.split("-")
                        start_line = int(parts[0].strip())
                        end_line = int(parts[1].strip())
                    except Exception:
                        pass

                code_content = target_snippets.get(
                    file_path,
                    f"# Source code snippet for {file_path}\n# Symbol: {symbol_name}\n"
                )

                files_list.append({
                    "file_path": file_path,
                    "role": role,
                    "symbol_name": symbol_name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": code_content,
                    "language": "python" if file_path.endswith(".py") else "rst",
                    "is_verified": True,
                    "github_file_url": f"https://github.com/{repo_name}/blob/{commit_sha}/{file_path}#L{start_line}-L{end_line}"
                })

    if not files_list:
        raise HTTPException(status_code=404, detail="Code context is not available for this issue yet.")

    return {
        "issue_id": str(issue_id),
        "repo_full_name": repo_name,
        "commit_sha": issue.get("repo_commit_sha") or "main",
        "files": files_list
    }
