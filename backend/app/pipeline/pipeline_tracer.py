"""
GitNova Pipeline Observability & Structured Tracer.

Provides high-resolution, end-to-end diagnostic tracing for every raw issue discovered
by the GitHub ingestion pipeline, tracking each issue through all 10 evaluation stages.
"""

import os
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List


# Base trace directory
TRACES_BASE_DIR = Path(__file__).resolve().parents[3] / "traces"


class PipelineTracer:
    """
    Structured, zero-dependency diagnostic tracer for GitNova ingestion pipelines.
    Guarantees that EVERY raw issue discovered by GitHub API receives a persistent trace record.
    """

    def __init__(self, run_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        if not run_id:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
            short_hash = os.urandom(3).hex()
            self.run_id = f"{now_str}_{short_hash}"
        else:
            self.run_id = run_id

        self.start_time = time.time()
        self.metadata = metadata or {}
        self.run_dir = TRACES_BASE_DIR / "runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (TRACES_BASE_DIR / "summaries").mkdir(parents=True, exist_ok=True)

        self.trace_records: Dict[str, Dict[str, Any]] = {}
        self.jsonl_path = self.run_dir / "trace.jsonl"
        self.csv_path = self.run_dir / "trace.csv"
        self.summary_json_path = self.run_dir / "summary.json"
        self.summary_md_path = self.run_dir / "summary.md"


        # Initialize README if missing
        self._ensure_readme()

    def _ensure_readme(self):
        readme_path = TRACES_BASE_DIR / "README.md"
        if not readme_path.exists():
            try:
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(
                        "# GitNova Diagnostic Pipeline Traces\n\n"
                        "This directory contains high-resolution observability traces generated during "
                        "GitNova pipeline runs.\n\n"
                        "## Structure\n"
                        "- `runs/<run_id>/trace.jsonl`: Line-delimited JSON of all raw issues discovered and their funnel stages.\n"
                        "- `runs/<run_id>/summary.json`: Aggregated funnel statistics for the run.\n"
                        "- `runs/<run_id>/summary.md`: Human-readable funnel report.\n"
                    )
            except Exception:
                pass

    def _get_trace_id(self, repo_full_name: str, issue_number: int) -> str:
        return f"{self.run_id}:{repo_full_name}#{issue_number}"

    def record_stage_1_discovery(
        self,
        repo_full_name: str,
        raw_issue: Dict[str, Any],
        repo_id: Optional[str] = None,
        page_number: int = 1,
        discovery_source: str = "github_api_paginated",
        language: Optional[str] = None
    ) -> str:
        """
        Stage 1: Record initial discovery of a raw GitHub issue before any filtering.
        """
        issue_number = raw_issue.get("number") or 0
        trace_id = self._get_trace_id(repo_full_name, issue_number)

        labels = [l.get("name") if isinstance(l, dict) else str(l) for l in raw_issue.get("labels", []) if l]
        assignees = [a.get("login") if isinstance(a, dict) else str(a) for a in raw_issue.get("assignees", []) if a]
        is_pr = "pull_request" in raw_issue or "/pull/" in raw_issue.get("html_url", "")

        record = {
            "run_id": self.run_id,
            "trace_id": trace_id,
            "repository": repo_full_name,
            "repo_id": repo_id,
            "language": language or "Unknown",
            "github_issue_number": issue_number,
            "github_url": raw_issue.get("html_url", f"https://github.com/{repo_full_name}/issues/{issue_number}"),
            "title": raw_issue.get("title", ""),
            "body_length": len(raw_issue.get("body") or ""),
            "state": raw_issue.get("state", "open"),
            "author": raw_issue.get("user", {}).get("login", "unknown") if isinstance(raw_issue.get("user"), dict) else "unknown",
            "labels": labels,
            "assignees": assignees,
            "is_pull_request": is_pr,
            "comments_count": int(raw_issue.get("comments") or 0),
            "created_at": raw_issue.get("created_at"),
            "updated_at": raw_issue.get("updated_at"),
            "discovery_timestamp": datetime.now(timezone.utc).isoformat(),
            "discovery_source": discovery_source,
            "page_number": page_number,
            
            # Stage records
            "stage_1_discovery": "PASS",
            "stage_2_prefilter": None,
            "stage_3_repository_context": None,
            "stage_4_rag": None,
            "stage_5_evidence": None,
            "stage_6_gemini": {"called": False},
            "stage_7_grounding": None,
            "stage_8_publication": None,
            "stage_9_database": None,
            "final_state": "DISCOVERED"
        }

        self.trace_records[trace_id] = record
        self._append_jsonl(record)
        return trace_id

    def record_stage_2_prefilter(
        self,
        trace_id: str,
        passed: bool,
        rule_id: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Stage 2: Record deterministic pre-filter outcome."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        if passed:
            rec["stage_2_prefilter"] = {"decision": "PASS"}
        else:
            rec["stage_2_prefilter"] = {
                "decision": "REJECT",
                "rule_id": rule_id or "UNKNOWN_RULE",
                "reason": reason or "Failed deterministic pre-filter",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            rec["final_state"] = "REJECTED_STAGE_2"
        self._flush_record(trace_id)

    def record_stage_3_repository_context(
        self,
        trace_id: str,
        passed: bool,
        commit_sha: Optional[str] = None,
        is_reused: bool = True,
        reason: Optional[str] = None
    ):
        """Stage 3: Record repository indexing and snapshot resolution."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        if passed:
            rec["stage_3_repository_context"] = {
                "decision": "PASS",
                "commit_sha": commit_sha,
                "index_reused": is_reused
            }
        else:
            rec["stage_3_repository_context"] = {
                "decision": "REJECT",
                "reason": reason or "Failed repository context resolution",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            rec["final_state"] = "REJECTED_STAGE_3"
        self._flush_record(trace_id)

    def record_stage_4_rag(
        self,
        trace_id: str,
        passed: bool,
        vector_count: int = 0,
        lexical_count: int = 0,
        final_count: int = 0,
        retrieved_files: Optional[List[str]] = None,
        retrieved_symbols: Optional[List[str]] = None,
        reason: Optional[str] = None
    ):
        """Stage 4: Record RAG hybrid RRF code retrieval metrics."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        if passed:
            rec["stage_4_rag"] = {
                "decision": "PASS",
                "vector_candidate_count": vector_count,
                "lexical_candidate_count": lexical_count,
                "final_rrf_count": final_count,
                "retrieved_files": (retrieved_files or [])[:10],
                "retrieved_symbols": (retrieved_symbols or [])[:10]
            }
        else:
            rec["stage_4_rag"] = {
                "decision": "FAIL",
                "reason": reason or "RAG retrieval returned insufficient context",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            rec["final_state"] = "REJECTED_STAGE_4"
        self._flush_record(trace_id)

    def record_stage_5_evidence(
        self,
        trace_id: str,
        passed: bool,
        evidence_categories: Optional[Dict[str, bool]] = None,
        reason: Optional[str] = None
    ):
        """Stage 5: Record structured EvidencePackage construction."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        if passed:
            rec["stage_5_evidence"] = {
                "decision": "PASS",
                "categories_present": evidence_categories or {}
            }
        else:
            rec["stage_5_evidence"] = {
                "decision": "FAIL",
                "reason": reason or "Failed to build structured EvidencePackage",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            rec["final_state"] = "REJECTED_STAGE_5"
        self._flush_record(trace_id)

    def record_stage_6_gemini(
        self,
        trace_id: str,
        called: bool,
        model: Optional[str] = None,
        latency_ms: float = 0.0,
        difficulty_tier: Optional[str] = None,
        difficulty_reasoning: Optional[str] = None,
        availability_decision: Optional[str] = None,
        availability_reasoning: Optional[str] = None,
        beginner_suitability_decision: Optional[str] = None,
        publication_decision: Optional[str] = None,
        publication_reason: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Stage 6: Record Gemini model investigation and classification result."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        if called:
            rec["stage_6_gemini"] = {
                "called": True,
                "model": model,
                "latency_ms": round(latency_ms, 2),
                "difficulty_tier": difficulty_tier,
                "difficulty_reasoning": difficulty_reasoning,
                "availability_decision": availability_decision,
                "availability_reasoning": availability_reasoning,
                "beginner_suitability_decision": beginner_suitability_decision,
                "publication_decision": publication_decision,
                "publication_reason": publication_reason,
                "error": error
            }
        else:
            rec["stage_6_gemini"] = {
                "called": False,
                "reason": error or "Skipped (pre-filter or cache hit)"
            }
        self._flush_record(trace_id)

    def record_stage_7_grounding(
        self,
        trace_id: str,
        passed: bool,
        status: Optional[str] = None,
        verified_count: int = 0,
        hallucinated_count: int = 0,
        reasons: Optional[List[str]] = None
    ):
        """Stage 7: Record AST Grounding verification outcome."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        if passed:
            rec["stage_7_grounding"] = {
                "decision": "PASS",
                "status": status or "VERIFIED",
                "verified_citations": verified_count,
                "pruned_citations": hallucinated_count
            }
        else:
            rec["stage_7_grounding"] = {
                "decision": "FAIL",
                "status": status or "UNVERIFIED",
                "reasons": reasons or [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            rec["final_state"] = "REJECTED_STAGE_7"
        self._flush_record(trace_id)

    def record_stage_8_publication_gate(
        self,
        trace_id: str,
        final_gate: bool,
        criteria_breakdown: Optional[Dict[str, bool]] = None,
        rejection_reasons: Optional[List[str]] = None
    ):
        """Stage 8: Record 10-point fail-closed publication gate criteria."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        rec["stage_8_publication"] = {
            "final_gate": "PASS" if final_gate else "FAIL",
            "criteria_breakdown": criteria_breakdown or {},
            "rejection_reasons": rejection_reasons or []
        }

        if not final_gate:
            rec["final_state"] = "REJECTED_STAGE_8"
        self._flush_record(trace_id)

    def record_stage_9_database(
        self,
        trace_id: str,
        passed: bool,
        issue_id: Optional[str] = None,
        is_published: bool = False,
        quality_score: Optional[int] = None,
        mismatch: bool = False,
        reason: Optional[str] = None
    ):
        """Stage 9: Record Supabase persistence and verify DB state matches pipeline decision."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return

        rec["stage_9_database"] = {
            "decision": "PASS" if passed else "FAIL",
            "issue_id": issue_id,
            "is_published": is_published,
            "quality_score": quality_score,
            "database_state_mismatch": mismatch,
            "reason": reason
        }

        if is_published:
            rec["final_state"] = "PUBLISHED"
        elif rec.get("final_state") == "DISCOVERED":
            rec["final_state"] = "GATED"
        self._flush_record(trace_id)

    def record_final_error(self, trace_id: str, error_msg: str):
        """Record unhandled execution error."""
        rec = self.trace_records.get(trace_id)
        if not rec:
            return
        rec["final_state"] = "ERROR"
        rec["error"] = error_msg
        self._flush_record(trace_id)

    def _append_jsonl(self, record: Dict[str, Any]):
        try:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def _flush_record(self, trace_id: str):
        # Full rewrite of jsonl periodically or at end
        pass

    def finish_run(self) -> Dict[str, Any]:
        """
        Finalize pipeline run trace, write complete trace.jsonl, summary.json, and summary.md.
        """
        duration = round(time.time() - self.start_time, 2)
        total_discovered = len(self.trace_records)

        # Write complete trace.jsonl
        try:
            with open(self.jsonl_path, "w", encoding="utf-8") as f:
                for rec in self.trace_records.values():
                    f.write(json.dumps(rec) + "\n")
        except Exception as e:
            print(f"⚠️ Trace write error: {e}")

        # Compute funnel statistics
        s2_passed = sum(1 for r in self.trace_records.values() if (r.get("stage_2_prefilter") or {}).get("decision") == "PASS")
        s2_rejected = sum(1 for r in self.trace_records.values() if (r.get("stage_2_prefilter") or {}).get("decision") == "REJECT")

        s3_passed = sum(1 for r in self.trace_records.values() if (r.get("stage_3_repository_context") or {}).get("decision") == "PASS")
        s3_rejected = sum(1 for r in self.trace_records.values() if (r.get("stage_3_repository_context") or {}).get("decision") == "REJECT")

        s4_passed = sum(1 for r in self.trace_records.values() if (r.get("stage_4_rag") or {}).get("decision") == "PASS")
        s4_failed = sum(1 for r in self.trace_records.values() if (r.get("stage_4_rag") or {}).get("decision") == "FAIL")

        s5_passed = sum(1 for r in self.trace_records.values() if (r.get("stage_5_evidence") or {}).get("decision") == "PASS")
        s5_failed = sum(1 for r in self.trace_records.values() if (r.get("stage_5_evidence") or {}).get("decision") == "FAIL")

        gemini_called = sum(1 for r in self.trace_records.values() if (r.get("stage_6_gemini") or {}).get("called") is True)
        gemini_skipped = total_discovered - gemini_called

        s7_passed = sum(1 for r in self.trace_records.values() if (r.get("stage_7_grounding") or {}).get("decision") == "PASS")
        s7_failed = sum(1 for r in self.trace_records.values() if (r.get("stage_7_grounding") or {}).get("decision") == "FAIL")

        s8_passed = sum(1 for r in self.trace_records.values() if (r.get("stage_8_publication") or {}).get("final_gate") == "PASS")
        s8_rejected = sum(1 for r in self.trace_records.values() if (r.get("stage_8_publication") or {}).get("final_gate") == "FAIL")

        published = sum(1 for r in self.trace_records.values() if r.get("final_state") == "PUBLISHED")
        errors = sum(1 for r in self.trace_records.values() if r.get("final_state") == "ERROR")
        rejected_total = total_discovered - published - errors

        # Aggregate rejection reasons
        rejection_reasons: Dict[str, int] = {}
        for r in self.trace_records.values():
            s2 = r.get("stage_2_prefilter") or {}
            if s2.get("decision") == "REJECT":
                rule = s2.get("rule_id", "PREFILTER_UNKNOWN")
                rejection_reasons[rule] = rejection_reasons.get(rule, 0) + 1
            
            s8 = r.get("stage_8_publication") or {}
            if s8.get("final_gate") == "FAIL":
                for r_reason in s8.get("rejection_reasons", []):
                    rejection_reasons[r_reason] = rejection_reasons.get(r_reason, 0) + 1

        summary = {
            "run_id": self.run_id,
            "duration_seconds": duration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": self.metadata,
            "funnel": {
                "raw_discovered": total_discovered,
                "stage_2_prefilter": {"passed": s2_passed, "rejected": s2_rejected},
                "stage_3_repository_context": {"passed": s3_passed, "rejected": s3_rejected},
                "stage_4_rag": {"passed": s4_passed, "failed": s4_failed},
                "stage_5_evidence": {"passed": s5_passed, "failed": s5_failed},
                "stage_6_gemini": {"called": gemini_called, "not_called": gemini_skipped},
                "stage_7_grounding": {"passed": s7_passed, "failed": s7_failed},
                "stage_8_publication": {"passed": s8_passed, "rejected": s8_rejected},
                "final_verdict": {
                    "published": published,
                    "rejected": rejected_total,
                    "errors": errors
                }
            },
            "rejection_breakdown": rejection_reasons
        }

        # Write summary.json
        try:
            with open(self.summary_json_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        except Exception:
            pass

        # Write summary.md
        try:
            self._write_summary_md(summary)
        except Exception:
            pass

        # Write trace.csv
        try:
            self._write_trace_csv()
        except Exception as csv_err:
            print(f"⚠️ Trace CSV write warning: {csv_err}")

        return summary

    def _write_trace_csv(self):
        """
        Write tabular trace.csv matching the exact diagnostic schema.
        """
        fieldnames = [
            "run_id",
            "trace_id",
            "repo",
            "issue_number",
            "issue_url",
            "stage_1_discovered",
            "discovery_page",
            "discovery_language",
            "stage_2_decision",
            "stage_2_rule_id",
            "stage_2_rule_name",
            "stage_2_reason",
            "stage_3_decision",
            "snapshot_id",
            "commit_sha",
            "index_reused",
            "stage_4_decision",
            "vector_count",
            "lexical_count",
            "rrf_count",
            "retrieved_files",
            "retrieved_symbols",
            "stage_5_decision",
            "evidence_completeness",
            "stage_6_gemini_called",
            "gemini_model",
            "gemini_latency_ms",
            "gemini_retry_count",
            "gemini_rate_limited",
            "gemini_difficulty",
            "gemini_availability",
            "gemini_suitability",
            "gemini_evidence_sufficiency",
            "gemini_publication",
            "stage_7_grounding",
            "grounding_reason",
            "stage_8_gate",
            "gate_failed_criteria",
            "stage_9_database",
            "database_status",
            "final_state"
        ]

        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for rec in self.trace_records.values():
                s2 = rec.get("stage_2_prefilter") or {}
                s3 = rec.get("stage_3_repository_context") or {}
                s4 = rec.get("stage_4_rag") or {}
                s5 = rec.get("stage_5_evidence") or {}
                s6 = rec.get("stage_6_gemini") or {}
                s7 = rec.get("stage_7_grounding") or {}
                s8 = rec.get("stage_8_publication") or {}
                s9 = rec.get("stage_9_database") or {}

                row = {
                    "run_id": rec.get("run_id", ""),
                    "trace_id": rec.get("trace_id", ""),
                    "repo": rec.get("repository", ""),
                    "issue_number": rec.get("github_issue_number", 0),
                    "issue_url": rec.get("github_url", ""),
                    "stage_1_discovered": "TRUE",
                    "discovery_page": rec.get("page_number", 1),
                    "discovery_language": rec.get("language") or rec.get("discovery_language") or "Unknown",
                    "stage_2_decision": s2.get("decision", "SKIPPED") if rec.get("stage_2_prefilter") else "SKIPPED",
                    "stage_2_rule_id": s2.get("rule_id", ""),
                    "stage_2_rule_name": s2.get("rule_id", ""),
                    "stage_2_reason": s2.get("reason", ""),
                    "stage_3_decision": s3.get("decision", "SKIPPED") if rec.get("stage_3_repository_context") else "SKIPPED",
                    "snapshot_id": s3.get("snapshot_id", ""),
                    "commit_sha": s3.get("commit_sha", ""),
                    "index_reused": s3.get("index_reused", False),
                    "stage_4_decision": s4.get("decision", "SKIPPED") if rec.get("stage_4_rag") else "SKIPPED",
                    "vector_count": s4.get("vector_candidate_count", 0),
                    "lexical_count": s4.get("lexical_candidate_count", 0),
                    "rrf_count": s4.get("final_rrf_count", 0),
                    "retrieved_files": "; ".join(s4.get("retrieved_files", [])),
                    "retrieved_symbols": "; ".join(s4.get("retrieved_symbols", [])),
                    "stage_5_decision": s5.get("decision", "SKIPPED") if rec.get("stage_5_evidence") else "SKIPPED",
                    "evidence_completeness": "; ".join(f"{k}={v}" for k, v in s5.get("categories_present", {}).items()),
                    "stage_6_gemini_called": s6.get("called", False),
                    "gemini_model": s6.get("model", ""),
                    "gemini_latency_ms": s6.get("latency_ms", 0),
                    "gemini_retry_count": s6.get("retry_count", 0),
                    "gemini_rate_limited": s6.get("rate_limited", False),
                    "gemini_difficulty": s6.get("difficulty_tier", ""),
                    "gemini_availability": s6.get("availability_decision", ""),
                    "gemini_suitability": s6.get("beginner_suitability_decision", ""),
                    "gemini_evidence_sufficiency": s6.get("evidence_sufficiency", ""),
                    "gemini_publication": s6.get("publication_decision", ""),
                    "stage_7_grounding": s7.get("status", "SKIPPED") if rec.get("stage_7_grounding") else "SKIPPED",
                    "grounding_reason": "; ".join(s7.get("reasons", [])),
                    "stage_8_gate": s8.get("final_gate", "SKIPPED") if rec.get("stage_8_publication") else "SKIPPED",
                    "gate_failed_criteria": "; ".join(s8.get("rejection_reasons", [])),
                    "stage_9_database": s9.get("decision", "SKIPPED") if rec.get("stage_9_database") else "SKIPPED",
                    "database_status": s9.get("reason") or ("SUCCESS" if s9.get("decision") == "PASS" else "SKIPPED"),
                    "final_state": rec.get("final_state", "UNKNOWN")
                }
                writer.writerow(row)


    def _write_summary_md(self, summary: Dict[str, Any]):
        f = summary["funnel"]
        reasons = summary["rejection_breakdown"]

        md_lines = [
            f"# Pipeline Run Summary: `{self.run_id}`\n\n",
            f"- **Execution Date:** `{summary['timestamp']}`\n",
            f"- **Total Duration:** `{summary['duration_seconds']}s`\n",
            f"- **Total Raw Issues Discovered:** **`{f['raw_discovered']}`**\n\n",
            "## 📉 End-to-End Pipeline Funnel\n\n",
            "| Funnel Stage | Passed / Called | Rejected / Failed |\n",
            "| :--- | :--- | :--- |\n",
            f"| **1. Raw GitHub Discovery** | `{f['raw_discovered']}` | `0` |\n",
            f"| **2. Deterministic Pre-filter** | `{f['stage_2_prefilter']['passed']}` | `{f['stage_2_prefilter']['rejected']}` |\n",
            f"| **3. Repository Context / Snapshot** | `{f['stage_3_repository_context']['passed']}` | `{f['stage_3_repository_context']['rejected']}` |\n",
            f"| **4. Hybrid RAG Retrieval** | `{f['stage_4_rag']['passed']}` | `{f['stage_4_rag']['failed']}` |\n",
            f"| **5. Evidence Package Builder** | `{f['stage_5_evidence']['passed']}` | `{f['stage_5_evidence']['failed']}` |\n",
            f"| **6. Gemini Model Investigation** | `{f['stage_6_gemini']['called']}` | `{f['stage_6_gemini']['not_called']}` |\n",
            f"| **7. AST Grounding Verification** | `{f['stage_7_grounding']['passed']}` | `{f['stage_7_grounding']['failed']}` |\n",
            f"| **8. 10-Point Publication Gate** | `{f['stage_8_publication']['passed']}` | `{f['stage_8_publication']['rejected']}` |\n",
            f"| **FINAL RESULT** | **`{f['final_verdict']['published']} PUBLISHED`** ✅ | **`{f['final_verdict']['rejected']} REJECTED`** 🛡️ (`{f['final_verdict']['errors']} errors`) |\n\n",
            "## 🛑 Rejection Reasons Breakdown\n\n"
        ]

        if reasons:
            md_lines.append("| Rejection Rule / Reason | Count |\n| :--- | :--- |\n")
            for r_name, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
                md_lines.append(f"| `{r_name}` | **{count}** |\n")
        else:
            md_lines.append("*No issues rejected.*\n")

        md_lines.append("\n---\n*Generated automatically by GitNova PipelineTracer.*\n")

        with open(self.summary_md_path, "w", encoding="utf-8") as f:
            f.writelines(md_lines)


# Global tracer singleton accessor
_GLOBAL_TRACER: Optional[PipelineTracer] = None


def get_current_tracer() -> Optional[PipelineTracer]:
    global _GLOBAL_TRACER
    return _GLOBAL_TRACER


def set_current_tracer(tracer: Optional[PipelineTracer]):
    global _GLOBAL_TRACER
    _GLOBAL_TRACER = tracer
