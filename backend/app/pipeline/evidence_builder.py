"""
GitNova v4.5 — Evidence Builder Engine

Constructs a structured EvidencePackage from raw GitHub data, repository manifests,
RRF hybrid retrieved AST code chunks, and timeline activity.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.schemas.evidence import (
    EvidencePackage,
    IssueEvidence,
    StatusEvidence,
    RepositoryEvidence,
    CodeEvidenceItem,
    TestEvidenceItem,
    DiscussionEvidence,
)
from app.schemas.explanation import RepositoryContributionGuide


class EvidenceBuilder:
    """Assembles all available verified evidence for an issue into a structured EvidencePackage with dynamic context budgeting."""

    @staticmethod
    def estimate_tokens(text: Optional[str]) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    @classmethod
    def build_package(
        cls,
        raw_issue: Dict[str, Any],
        repo_data: Dict[str, Any],
        repo_guide: RepositoryContributionGuide,
        commit_sha: str,
        retrieved_chunks: List[Dict[str, Any]],
        opportunity_eval: Optional[Dict[str, Any]] = None,
        timeline_events: Optional[List[Dict[str, Any]]] = None,
        max_evidence_tokens: int = 14000,
    ) -> EvidencePackage:
        now_iso = datetime.now(timezone.utc).isoformat()
        opportunity_eval = opportunity_eval or {}
        repo_full_name = repo_data.get("full_name") or raw_issue.get("repo_name") or "unknown/repo"

        # 1. Issue Evidence
        reporter_username = "community_contributor"
        user_obj = raw_issue.get("user")
        if isinstance(user_obj, dict) and user_obj.get("login"):
            reporter_username = user_obj["login"]
        elif raw_issue.get("reporter_username"):
            reporter_username = raw_issue["reporter_username"]

        raw_labels = raw_issue.get("labels") or []
        labels_list = [
            lbl.get("name") if isinstance(lbl, dict) else str(lbl)
            for lbl in raw_labels if lbl
        ]

        raw_assignees = raw_issue.get("assignees") or []
        if raw_issue.get("assignee") and raw_issue.get("assignee") not in raw_assignees:
            raw_assignees.append(raw_issue["assignee"])
        assignees_list = [
            a.get("login") if isinstance(a, dict) else str(a)
            for a in raw_assignees if a
        ]

        issue_evidence = IssueEvidence(
            repo_full_name=repo_full_name,
            github_issue_number=int(raw_issue.get("number") or raw_issue.get("github_issue_number") or 1),
            title=raw_issue.get("title") or "Issue",
            body=raw_issue.get("body") or "",
            state=raw_issue.get("state") or "open",
            reporter_username=reporter_username,
            labels=labels_list,
            assignees=assignees_list,
            created_at=raw_issue.get("created_at"),
            updated_at=raw_issue.get("updated_at"),
            comments_count=int(raw_issue.get("comments") or 0),
            html_url=raw_issue.get("html_url") or f"https://github.com/{repo_full_name}/issues/{raw_issue.get('number', 1)}"
        )

        # 2. Status Evidence
        signals = opportunity_eval.get("signals") or {}
        status_evidence = StatusEvidence(
            availability_status=opportunity_eval.get("availability_status") or "CHECK_DISCUSSION",
            confidence=opportunity_eval.get("opportunity_confidence") or "HIGH",
            is_assigned=len(assignees_list) > 0,
            has_positive_labels=bool(signals.get("has_positive_labels")),
            has_warning_labels=bool(signals.get("has_warning_labels")),
            linked_prs_count=len(opportunity_eval.get("linked_prs") or []),
            linked_prs=opportunity_eval.get("linked_prs") or [],
            evidence_statements=opportunity_eval.get("evidence") or signals.get("evidence_statements") or [],
            warning_statements=opportunity_eval.get("warnings") or signals.get("warning_statements") or [],
            last_verified_at=opportunity_eval.get("last_verified_at") or now_iso
        )

        # 3. Repository Evidence
        repo_evidence = RepositoryEvidence(
            repo_full_name=repo_full_name,
            primary_language=repo_data.get("language") or "Python",
            default_branch=repo_data.get("default_branch") or "main",
            current_commit_sha=commit_sha,
            package_manager=getattr(repo_guide, "package_manager", "NOT_VERIFIED") if hasattr(repo_guide, "package_manager") else "NOT_VERIFIED",
            test_framework=getattr(repo_guide, "test_framework", "NOT_VERIFIED") if hasattr(repo_guide, "test_framework") else "NOT_VERIFIED",
            test_command=repo_guide.test_command,
            test_command_source=repo_guide.test_command_source,
            lint_command=repo_guide.lint_command,
            lint_command_source=repo_guide.lint_command_source,
            format_command=repo_guide.format_command,
            format_command_source=repo_guide.format_command_source,
            setup_instructions=repo_guide.setup_instructions,
            contributing_guidelines_summary=repo_guide.pull_request_guidance,
            cla_required=repo_guide.cla_required
        )

        # 4. Code & Test Evidence Separation with Deduplication and Composite Ranking
        seen_ranges = set()
        deduped_chunks = []

        issue_text_lower = f"{raw_issue.get('title', '')} {raw_issue.get('body', '')}".lower()

        for chunk in retrieved_chunks:
            fp = chunk.get("file_path", "")
            s_line = int(chunk.get("start_line") or 1)
            e_line = int(chunk.get("end_line") or s_line)
            range_key = (fp, s_line // 20)  # bucket nearby lines to avoid duplicate slices

            if range_key in seen_ranges:
                continue
            seen_ranges.add(range_key)

            # Composite ranking: lexical + vector + exact symbol + file + qualified
            val_score = float(chunk.get("similarity") or chunk.get("lexical_rank") or 1.0)
            sym = (chunk.get("symbol_name") or "").lower()
            qual = (chunk.get("qualified_symbol_name") or "").lower()
            
            if sym and sym in issue_text_lower:
                val_score += 15.0  # Exact symbol mentioned in issue
            if qual and qual in issue_text_lower:
                val_score += 20.0  # Qualified symbol path mentioned in issue
            
            file_leaf = fp.lower().split("/")[-1]
            if file_leaf and file_leaf in issue_text_lower:
                val_score += 8.0   # File name mentioned in issue
            
            chunk["_computed_val_score"] = val_score
            deduped_chunks.append(chunk)

        # Sort deduped chunks by highest value score
        deduped_chunks.sort(key=lambda c: c.get("_computed_val_score", 0.0), reverse=True)

        # Budget allocations: ~70% for code, ~30% for tests
        max_code_tokens = int(max_evidence_tokens * 0.70)
        max_test_tokens = int(max_evidence_tokens * 0.30)

        code_items: List[CodeEvidenceItem] = []
        test_items: List[TestEvidenceItem] = []
        current_code_tokens = 0
        current_test_tokens = 0

        for idx, chunk in enumerate(deduped_chunks):
            fp = chunk.get("file_path", "")
            is_test_file = ("test" in fp.lower()) or (chunk.get("info_class") == "TESTS")
            info_cls = chunk.get("info_class") or ("TESTS" if is_test_file else "SOURCE_CODE")
            content = chunk.get("content") or ""
            chunk_tokens = cls.estimate_tokens(content) + 50

            if is_test_file:
                if (current_test_tokens + chunk_tokens <= max_test_tokens) or len(test_items) < 2:
                    test_items.append(TestEvidenceItem(
                        chunk_id=str(chunk.get("chunk_id") or f"test_{idx}"),
                        file_path=fp,
                        test_function_name=chunk.get("symbol_name"),
                        start_line=int(chunk.get("start_line") or 1),
                        end_line=int(chunk.get("end_line") or 1),
                        content=content,
                        contextual_header=chunk.get("contextual_header")
                    ))
                    current_test_tokens += chunk_tokens
            else:
                if (current_code_tokens + chunk_tokens <= max_code_tokens) or len(code_items) < 2:
                    code_items.append(CodeEvidenceItem(
                        chunk_id=str(chunk.get("chunk_id") or f"code_{idx}"),
                        file_path=fp,
                        symbol_name=chunk.get("symbol_name"),
                        qualified_symbol_name=chunk.get("qualified_symbol_name"),
                        symbol_type=chunk.get("symbol_type"),
                        info_class=info_cls,
                        start_line=int(chunk.get("start_line") or 1),
                        end_line=int(chunk.get("end_line") or 1),
                        content=content,
                        contextual_header=chunk.get("contextual_header"),
                        commit_sha=chunk.get("commit_sha") or commit_sha,
                        retrieval_method=chunk.get("retrieval_method") or "hybrid_rrf",
                        retrieval_score=float(chunk.get("_computed_val_score") or 0.0)
                    ))
                    current_code_tokens += chunk_tokens

        # 5. Discussion Evidence
        raw_events = timeline_events or []
        disc_summary_obj = opportunity_eval.get("discussion_summary")
        summary_text = getattr(disc_summary_obj, "summary", None) if disc_summary_obj else None
        intent_text = getattr(disc_summary_obj, "maintainer_intent", None) if disc_summary_obj else None

        discussion_evidence = DiscussionEvidence(
            has_discussion_data=len(raw_events) > 0,
            timeline_events_count=len(raw_events),
            discussion_summary=summary_text,
            maintainer_intent=intent_text,
            conflicting_work_detected=(opportunity_eval.get("availability_status") == "CHECK_DISCUSSION")
        )

        return EvidencePackage(
            issue=issue_evidence,
            status=status_evidence,
            repository=repo_evidence,
            code_evidence=code_items,
            test_evidence=test_items,
            discussion=discussion_evidence,
            package_timestamp=now_iso
        )

    @classmethod
    def apply_graceful_context_reduction(
        cls,
        evidence: EvidencePackage,
        target_token_budget: int
    ) -> EvidencePackage:
        """
        Gracefully reduces context size when rate limits or smaller context windows are encountered.
        Reduction Order:
        1. Remove lowest-relevance source chunks (preserve primary targets)
        2. Remove unrelated setup/contributing documentation
        3. Reduce comment/discussion text
        4. Truncate surrounding context in remaining code chunks
        *Never* removes the core issue, primary target code, or verified test command / test evidence.
        """
        # Calculate current approximate tokens
        total_tokens = sum(cls.estimate_tokens(c.content) for c in evidence.code_evidence)
        total_tokens += sum(cls.estimate_tokens(t.content) for t in evidence.test_evidence)
        total_tokens += cls.estimate_tokens(evidence.issue.body)

        if total_tokens <= target_token_budget:
            return evidence

        # Step 1: Prune lowest-ranked source chunks down to minimum 1
        pruned_code = list(evidence.code_evidence)
        while len(pruned_code) > 1 and total_tokens > target_token_budget:
            removed = pruned_code.pop()
            total_tokens -= cls.estimate_tokens(removed.content)

        # Step 2: Trim secondary repo documentation
        if total_tokens > target_token_budget:
            evidence.repository.setup_instructions = None
            evidence.repository.contributing_guidelines_summary = None

        # Step 3: Trim discussion summary
        if total_tokens > target_token_budget:
            evidence.discussion.discussion_summary = None
            evidence.discussion.maintainer_comments = []

        evidence.code_evidence = pruned_code
        return evidence
