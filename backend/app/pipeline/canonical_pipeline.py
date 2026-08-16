"""
GitNova v4.4.1 — Single Canonical Ingestion Pipeline Gateway

The authoritative, single entry point for processing and publishing GitHub issues.
Ensures zero bypasses:
  1. Validates canonical identity via DataIntegrityFirewall.
  2. Evaluates contribution opportunity, assignees, labels, timeline PRs, and discussion claims.
  3. Indexes repository codebase (Commit-SHA gated).
  4. Retrieves grounded code chunks via hybrid dense+sparse RRF.
  5. Computes deterministic difficulty and multi-dimensional beginner suitability.
  6. Generates LLM explanation.
  7. Verifies grounding citations against indexed chunks (pruning hallucinated paths).
  8. Extracts repository contribution guide (setup, test, lint commands).
  9. Generates 10-stage ContributionJourney with deterministic diagrams and provenance.
 10. Persists to Supabase with strict publication firewall (fails closed).
"""

import os
import sys
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

from app.core.config import settings
from app.pipeline.github_client import GitHubClient
from app.pipeline.data_integrity_firewall import DataIntegrityFirewall
from app.pipeline.pre_filter import pre_filter_issue
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator
from app.pipeline.code_indexer import ensure_repo_indexed
from app.pipeline.code_retriever import retrieve_chunks_for_issue
from app.pipeline.difficulty_engine import compute_issue_difficulty
from app.pipeline.issue_explainer import generate_issue_explanation
from app.pipeline.grounding_verifier import GroundingVerifier
from app.pipeline.quality_scorer import compute_quality_score
from app.pipeline.repo_guide_extractor import RepoGuideExtractor
from app.pipeline.journey_generator import ContributionJourneyGenerator


class CanonicalIngestionPipeline:
    """The single canonical gateway for processing and publishing GitHub issues."""

    @classmethod
    def ingest_and_process_issue(
        cls,
        repo_full_name: str,
        github_issue_number: int,
        supabase_client: Optional[Any] = None,
        github_client: Optional[GitHubClient] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the complete canonical pipeline for a single issue.
        Guarantees that no unverified or synthetic issue can be published.
        """
        if supabase_client is None:
            from supabase import create_client
            supabase_client = create_client(settings.supabase_url, settings.supabase_key)

        github = github_client or GitHubClient(supabase_client=supabase_client)
        now_iso = datetime.now(timezone.utc).isoformat()

        # Step 1: Fetch raw canonical issue from GitHub API
        issue_url = f"https://api.github.com/repos/{repo_full_name}/issues/{github_issue_number}"
        try:
            raw_issue = github.get(issue_url)
            if not isinstance(raw_issue, dict):
                return {
                    "success": False,
                    "published": False,
                    "rejection_stage": "GITHUB_FETCH",
                    "reason": f"Non-dict response from GitHub for {repo_full_name} #{github_issue_number}"
                }
        except Exception as e:
            return {
                "success": False,
                "published": False,
                "rejection_stage": "GITHUB_FETCH",
                "reason": f"GitHub API fetch error: {str(e)}"
            }

        # Step 2: Canonical Identity & Firewall Gate
        firewall_res = DataIntegrityFirewall.verify_canonical_identity(
            repo_full_name=repo_full_name,
            github_issue_number=github_issue_number,
            raw_gh_data=raw_issue
        )
        if firewall_res["data_integrity_status"] != "VERIFIED":
            return {
                "success": False,
                "published": False,
                "rejection_stage": "FIREWALL_IDENTITY",
                "reason": firewall_res.get("rejection_reason")
            }

        # Step 3: Fetch Repository Metadata from DB or GitHub
        repo_resp = supabase_client.table("repos").select("*").eq("full_name", repo_full_name).execute()
        repo_data = repo_resp.data[0] if (repo_resp.data and len(repo_resp.data) > 0) else None

        if not repo_data:
            # Auto-register repository if missing
            try:
                gh_repo = github.get(f"https://api.github.com/repos/{repo_full_name}")
                repo_lang = (gh_repo.get("language") if isinstance(gh_repo, dict) else None) or "Python"
                if isinstance(gh_repo, dict):
                    repo_insert = {
                        "full_name": repo_full_name,
                        "stars": gh_repo.get("stargazers_count", 0),
                        "language": repo_lang,
                        "description": gh_repo.get("description") or "",
                        "is_active": True,
                        "score": 75,
                        "tier": "starter",
                        "score_grade": "a",
                        "complexity_estimate": 40.0
                    }
                    ins_res = supabase_client.table("repos").insert(repo_insert).execute()
                    repo_data = ins_res.data[0] if ins_res.data else repo_insert
            except Exception as e:
                print(f"⚠️ Repo registration warning for {repo_full_name}: {e}")
                repo_data = {"full_name": repo_full_name, "score": 75, "complexity_estimate": 40.0, "language": repo_lang if 'repo_lang' in locals() else "Python"}

        repo_id = repo_data.get("id")
        repo_complexity = float(repo_data.get("complexity_estimate") or 50.0)

        # Step 4: Pre-Filter Check (Rule-based noise filter)
        title = raw_issue.get("title", "")
        body = raw_issue.get("body") or ""
        labels = raw_issue.get("labels") or []
        pf_res = pre_filter_issue(title, body, labels)
        if not pf_res["pass"]:
            return {
                "success": False,
                "published": False,
                "rejection_stage": "PRE_FILTER",
                "reason": pf_res["reason"]
            }

        # Step 5: Timeline & Discussion Intelligence
        timeline_events = github.fetch_issue_timeline_events(repo_full_name, github_issue_number)
        
        # Step 6: Contribution Opportunity & Suitability Evaluation
        opp_eval = ContributionOpportunityEvaluator.evaluate_issue_opportunity(
            raw_issue=raw_issue,
            repo_data=repo_data,
            timeline_events=timeline_events
        )

        reporter_username = opp_eval["reporter_username"]
        opportunity_confidence = opp_eval["opportunity_confidence"]
        opportunity_signals = opp_eval["signals"]
        availability_status = opp_eval.get("availability_status", "LIKELY_AVAILABLE")
        beginner_suitability = opp_eval.get("beginner_suitability")
        discussion_summary = opp_eval.get("discussion_summary")

        # Step 7: Commit-SHA Gated Codebase Indexing
        commit_sha = "main"
        try:
            commit_sha = ensure_repo_indexed(supabase_client, github, repo_full_name, repo_data)
        except Exception as idx_err:
            print(f"⚠️ Indexing notice for {repo_full_name}: {idx_err}")

        # Step 8: Hybrid RRF Code Retrieval
        retrieved_text, retrieved_chunks = retrieve_chunks_for_issue(
            supabase_client=supabase_client,
            repo_name=repo_full_name,
            commit_sha=commit_sha,
            issue_title=title,
            issue_body=body,
            max_tokens=10000,
            k_candidates=20,
            target_repo_id=None
        )

        # Step 9: Repository Guide Extraction (Language-Aware & Verified)
        contributing_md = github.fetch_repo_contributing_guide(repo_full_name) or ""
        repo_guide = RepoGuideExtractor.extract_guide(
            repo_full_name=repo_full_name,
            raw_contributing_md=contributing_md,
            language=repo_data.get("language")
        )

        # Step 10: Deterministic Difficulty Calculation (fallback only — LLM will override below)
        diff_score, diff_tier = compute_issue_difficulty(
            retrieved_chunks=retrieved_chunks,
            repo_complexity=repo_complexity,
            issue_body=body
        )

        # Step 11: Build Complete Structured EvidencePackage
        from app.pipeline.evidence_builder import EvidenceBuilder
        evidence_pkg = EvidenceBuilder.build_package(
            raw_issue=raw_issue,
            repo_data=repo_data,
            repo_guide=repo_guide,
            commit_sha=commit_sha,
            retrieved_chunks=retrieved_chunks,
            opportunity_eval=opp_eval,
            timeline_events=timeline_events
        )

        # Step 12: Grounded Multi-Phase LLM Explanation Generation (with Idempotent Caching)
        existing_cached_explanation = None
        if not dry_run and supabase_client:
            try:
                cached_query = supabase_client.table("issues").select("ai_hint, repo_commit_sha").eq("github_issue_number", github_issue_number)
                if repo_id:
                    cached_query = cached_query.eq("repo_id", repo_id)
                else:
                    cached_query = cached_query.eq("repo_name", repo_full_name)
                cached_res = cached_query.execute()
                if cached_res.data and cached_res.data[0].get("repo_commit_sha") == commit_sha:
                    hint_raw = cached_res.data[0].get("ai_hint")
                    if hint_raw:
                        hint_dict = json.loads(hint_raw) if isinstance(hint_raw, str) else hint_raw
                        if hint_dict.get("verification_status") == "VERIFIED" and hint_dict.get("summary") and hint_dict.get("relevant_locations"):
                            from app.schemas.explanation import IssueExplanation
                            existing_cached_explanation = IssueExplanation(**hint_dict)
                            print(f"⚡ [Cache] Reusing stored verified explanation for {repo_full_name} #{github_issue_number} at commit {commit_sha[:7]} (Zero LLM cost)")
            except Exception as c_err:
                print(f"⚠️ Cache check notice for {repo_full_name}: {c_err}")

        if existing_cached_explanation:
            explanation_obj = existing_cached_explanation
        else:
            explanation_obj = generate_issue_explanation(
                repo_name=repo_full_name,
                issue_title=title,
                issue_body=body,
                retrieved_chunks=retrieved_chunks,
                evidence_package=evidence_pkg
            )

        # Step 13: Grounding Verification (Prune hallucinated locations)
        verifier = GroundingVerifier(retrieved_chunks)
        explanation_obj = verifier.verify_and_sanitize(explanation_obj)
        verification_status, verification_reasons = verifier.compute_verification_status(explanation_obj)

        # Step 13b: Override difficulty_tier with LLM assessment (zero extra calls)
        llm_diff_tier = getattr(explanation_obj, "difficulty_tier", None)
        valid_tiers = {"BEGINNER", "INTERMEDIATE", "ADVANCED"}
        llm_difficulty_valid = llm_diff_tier and llm_diff_tier.upper() in valid_tiers

        if llm_difficulty_valid:
            diff_tier = llm_diff_tier.upper()
            llm_diff_reasoning = getattr(explanation_obj, "difficulty_reasoning", "")
            print(f"   🎯 [LLM Difficulty] {diff_tier} — {llm_diff_reasoning[:80]}...")
        else:
            # Do NOT fall back to deterministic — it's semantically unreliable.
            # Block publication instead so a mislabeled issue never reaches users.
            diff_tier = "INSUFFICIENT_EVIDENCE"
            print(f"   ⛔ [LLM Difficulty] Invalid tier '{llm_diff_tier}' — blocking publication (not falling back to heuristic).")

        # Step 14: 10-Stage Contribution Journey Generation
        journey_input = {
            "repo_full_name": repo_full_name,
            "github_issue_number": github_issue_number,
            "title": title,
            "reporter_username": reporter_username,
            "explanation": explanation_obj.model_dump() if hasattr(explanation_obj, "model_dump") else explanation_obj,
            "opportunity_signals": opportunity_signals,
            "availability_status": availability_status,
            "opportunity_confidence": opportunity_confidence,
            "beginner_suitability": beginner_suitability.model_dump() if hasattr(beginner_suitability, "model_dump") else beginner_suitability,
            "discussion_summary": discussion_summary.model_dump() if hasattr(discussion_summary, "model_dump") else discussion_summary,
            "last_verified_at": firewall_res["last_verified_at"]
        }
        journey = ContributionJourneyGenerator.generate_journey(
            issue_data=journey_input,
            repo_guide=repo_guide.model_dump() if hasattr(repo_guide, "model_dump") else repo_guide
        )

        # Step 15: Quality Scoring
        q_metrics = compute_quality_score(explanation_obj.summary or title, repo_data)
        quality_score = q_metrics["overall"]
        quality_grade = q_metrics["grade"]

        # Step 16: Publishing Firewall Gate (FAIL CLOSED)
        is_safe = (
            firewall_res["is_safe_to_publish"] and
            (verification_status == "VERIFIED") and
            opp_eval["is_eligible"] and
            (firewall_res["canonical_state"] == "open") and
            not firewall_res["is_pull_request"] and
            llm_difficulty_valid   # Block if LLM couldn't classify difficulty
        )

        chunk_ids = [c["chunk_id"] for c in retrieved_chunks if "chunk_id" in c]
        domain_topics = repo_data.get("topics") or []
        if repo_data.get("language"):
            domain_topics.append(repo_data["language"].lower())

        # Construct comprehensive JSON storage payload
        exp_dict = json.loads(explanation_obj.model_dump_json())
        exp_dict["beginner_suitability"] = beginner_suitability.model_dump() if hasattr(beginner_suitability, "model_dump") else beginner_suitability
        exp_dict["discussion_summary"] = discussion_summary.model_dump() if hasattr(discussion_summary, "model_dump") else discussion_summary
        exp_dict["contribution_journey"] = journey.model_dump() if hasattr(journey, "model_dump") else journey
        exp_dict["data_integrity_status"] = firewall_res["data_integrity_status"]
        exp_dict["freshness_status"] = firewall_res["freshness_status"]
        exp_dict["github_updated_at"] = firewall_res["github_updated_at"]
        exp_dict["last_verified_at"] = firewall_res["last_verified_at"]
        exp_dict["availability_status"] = availability_status
        exp_dict["verification_status"] = verification_status
        exp_dict["verification_reasons"] = verification_reasons

        # Construct comprehensive Supabase record payload matching exact database columns
        now_iso = datetime.now(timezone.utc).isoformat()
        deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_URL, firewall_res["canonical_url"]))
        issue_record = {
            "id": deterministic_id,
            "repo_id": repo_id,
            "repo_name": repo_full_name,
            "github_issue_number": github_issue_number,
            "title": firewall_res["canonical_title"],
            "url": firewall_res["canonical_url"],
            "status": firewall_res["canonical_state"],
            "difficulty": diff_tier,
            "ai_hint": json.dumps(exp_dict),
            "github_issue_updated_at": firewall_res["github_updated_at"],
            "repo_commit_sha": commit_sha,
            "retrieved_chunk_ids": chunk_ids,
            "retrieval_method": "hybrid_rrf",
            "quality_score": quality_score,
            "quality_grade": quality_grade.lower(),
            "freshness_label": firewall_res["freshness_status"],
            "is_published": is_safe,
            "updated_at": now_iso
        }

        if not dry_run:
            existing_query = supabase_client.table("issues").select("id").eq("github_issue_number", github_issue_number)
            if repo_id:
                existing_query = existing_query.eq("repo_id", repo_id)
            else:
                existing_query = existing_query.eq("repo_name", repo_full_name)
            
            existing_res = existing_query.execute()
            if existing_res.data:
                issue_id = existing_res.data[0]["id"]
                supabase_client.table("issues").update(issue_record).eq("id", issue_id).execute()
            else:
                supabase_client.table("issues").insert(issue_record).execute()

        return {
            "success": True,
            "published": is_safe,
            "repo_full_name": repo_full_name,
            "github_issue_number": github_issue_number,
            "title": firewall_res["canonical_title"],
            "availability_status": availability_status,
            "difficulty_tier": diff_tier,
            "suitability_score": beginner_suitability.score if hasattr(beginner_suitability, "score") else 75,
            "verification_status": verification_status,
            "firewall_status": firewall_res["data_integrity_status"]
        }
