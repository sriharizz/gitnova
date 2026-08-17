"""
GitNova v4.5 — Multi-Phase Evidence-Synthesizing Issue Explanation Engine

Transforms an EvidencePackage into a deeply grounded, beginner-friendly issue explanation
using a multi-phase reasoning pipeline:
  Phase 1: Code Investigation & Control Flow Reasoning (LLMInvestigationPayload)
  Phase 2: Grounded Planning & Minimal Change Strategy (LLMPlanPayload)
  Phase 3: Programmatic Grounding Verification & Citation Sanitization
"""

import json
from typing import List, Dict, Any, Optional, Union
from app.clients.llm.base import BaseLLMProvider
from app.clients.llm.factory import LLMProviderFactory
from app.pipeline.grounding_verifier import GroundingVerifier
from app.schemas.evidence import EvidencePackage
from app.schemas.explanation import (
    IssueExplanation,
    LLMInvestigationPayload,
    LLMPlanPayload,
    LLMIssueExplanationPayload,
    GroundedCodeLocation,
    GuidedSolutionStep,
    ConceptDetail,
)


def format_investigation_prompt(evidence: EvidencePackage) -> str:
    """Formats the EvidencePackage into an evidence-rich prompt for Phase 1 Code Investigation."""
    code_blocks = []
    for idx, c in enumerate(evidence.code_evidence, 1):
        header = c.contextual_header or f"[File: {c.file_path}]"
        sym_info = f" | Symbol: {c.qualified_symbol_name or c.symbol_name} ({c.symbol_type or 'code'})" if c.symbol_name else ""
        lines_info = f" | Lines: {c.start_line}-{c.end_line}"
        score_info = f" | Retrieval Score: {c.retrieval_score:.1f}" if c.retrieval_score else ""
        block = f"--- CODE EVIDENCE CHUNK {idx} [{c.info_class}]{sym_info}{lines_info}{score_info} ---\n{header}\n{c.content.strip()}\n"
        code_blocks.append(block)

    test_blocks = []
    for idx, t in enumerate(evidence.test_evidence, 1):
        header = t.contextual_header or f"[Test File: {t.file_path}]"
        fn_info = f" | Test Function: {t.test_function_name}" if t.test_function_name else ""
        lines_info = f" | Lines: {t.start_line}-{t.end_line}"
        block = f"--- TEST EVIDENCE CHUNK {idx}{fn_info}{lines_info} ---\n{header}\n{t.content.strip()}\n"
        test_blocks.append(block)

    code_context = "\n".join(code_blocks) if code_blocks else "No source code chunks retrieved."
    test_context = "\n".join(test_blocks) if test_blocks else "No specific test file chunks retrieved."

    # Discussion & Timeline Context
    disc_lines = []
    if evidence.discussion.maintainer_intent:
        disc_lines.append(f"Maintainer Intent: {evidence.discussion.maintainer_intent}")
    if evidence.discussion.discussion_summary:
        disc_lines.append(f"Discussion Summary: {evidence.discussion.discussion_summary}")
    if evidence.status.linked_prs_count > 0:
        disc_lines.append(f"Linked PRs Detected: {evidence.status.linked_prs_count} existing PR(s) reference this issue.")
    discussion_context = "\n".join(disc_lines) if disc_lines else "No active maintainer discussion or conflicting PRs reported."

    # Repository Guidelines
    guide_lines = [
        f"Primary Language: {evidence.repository.primary_language}",
        f"Default Branch: {evidence.repository.default_branch}",
        f"Commit Snapshot: {evidence.repository.current_commit_sha}",
        f"Verified Test Command: {evidence.repository.test_command} (Source: {evidence.repository.test_command_source})",
        f"Verified Lint Command: {evidence.repository.lint_command or 'NOT_VERIFIED'}",
    ]
    if evidence.repository.setup_instructions:
        guide_lines.append(f"Setup Instructions: {evidence.repository.setup_instructions[:300]}")
    if evidence.repository.contributing_guidelines_summary:
        guide_lines.append(f"Contribution Guidelines: {evidence.repository.contributing_guidelines_summary[:300]}")
    repo_guide_context = "\n".join(guide_lines)

    prompt = (
        f"You are a Senior Open-Source Maintainer and AI Code Investigator analyzing a real issue in repository '{evidence.issue.repo_full_name}'.\n\n"
        "=== GITHUB ISSUE CONTEXT ===\n"
        f"Repository: {evidence.issue.repo_full_name}\n"
        f"Issue Number: #{evidence.issue.github_issue_number}\n"
        f"Title: {evidence.issue.title}\n"
        f"Reporter: @{evidence.issue.reporter_username}\n"
        f"Labels: {', '.join(evidence.issue.labels) if evidence.issue.labels else 'None'}\n"
        f"Assignees: {', '.join(evidence.issue.assignees) if evidence.issue.assignees else 'Unassigned'}\n"
        f"State: {evidence.issue.state}\n"
        f"Issue Description:\n{evidence.issue.body or 'No body description provided.'}\n\n"
        "=== DISCUSSION & TIMELINE SIGNALS ===\n"
        f"{discussion_context}\n\n"
        "=== REPOSITORY ENVIRONMENT & GUIDELINES ===\n"
        f"{repo_guide_context}\n\n"
        "=== RETRIEVED SOURCE CODE EVIDENCE ===\n"
        f"{code_context}\n\n"
        "=== RETRIEVED TEST CODE EVIDENCE ===\n"
        f"{test_context}\n\n"
        "=== STRICT INVESTIGATION & SEMANTIC PUBLICATION INSTRUCTIONS ===\n"
        "1. Analyze the EXACT runtime control-flow path: Trace how input moves through the code and where the failure mechanism occurs.\n"
        "2. State what CURRENTLY happens at runtime and contrast it with what is EXPECTED to happen.\n"
        "3. Base all claims ONLY on the provided code evidence blocks. Never invent unverified files or functions.\n"
        "4. Include exact relative file paths, symbol names, and roles in 'relevant_locations' matching the code chunks.\n"
        "5. Identify existing relevant test files from the evidence or repository structure in 'relevant_test_files'.\n"
        "6. Create exactly 2 rich, issue-specific pedagogical concepts in 'structured_concepts'. Explain what it is, why it matters, and how it directly connects to fixing THIS specific issue.\n"
        "7. Highlight common pitfalls a beginner contributor must avoid.\n"
        "8. PROVENANCE RULE: Clearly distinguish VERIFIED_FACT (present in source code) from AI_INFERENCE (deduced mechanism) and MAINTAINER_INTENT (from maintainer comments). If evidence is insufficient for any claim, set evidence_sufficiency to INSUFFICIENT.\n"
        "9. DIFFICULTY CLASSIFICATION: Assess 'difficulty_tier' as exactly one of BEGINNER | BEGINNER_PLUS | INTERMEDIATE | ADVANCED:\n"
        "   - BEGINNER: fix touches 1-2 files, isolated logic, well-scoped, no domain expertise required (docs, typos, simple null-check, missing validation, straightforward test).\n"
        "   - BEGINNER_PLUS: well-scoped bug fix requiring straightforward unit test addition.\n"
        "   - INTERMEDIATE: requires understanding module internals, multi-file coordination, framework-specific knowledge, or non-trivial refactoring.\n"
        "   - ADVANCED: requires deep system knowledge, security implications, architectural decisions, cryptography, or broad refactoring.\n"
        "   Provide 'difficulty_reasoning' citing specific evidence from the code chunks.\n"
        "10. AVAILABILITY & MAINTAINER INTENT: Assess 'availability' as AVAILABLE | NOT_AVAILABLE | UNCERTAIN:\n"
        "   - NOT_AVAILABLE if discussion shows: handled internally, internal only, not open for external contributions, do not work on this, reserved for maintainers, already being handled in linked PRs, or not intended for external contributors.\n"
        "   - AVAILABLE only if open, unassigned, actionable, and welcoming external PRs.\n"
        "   - UNCERTAIN if ongoing debate or unclear maintainer consensus. Provide 'availability_reasoning'.\n"
        "11. BEGINNER SUITABILITY: Assess 'beginner_suitability' as SUITABLE | NOT_SUITABLE | UNCERTAIN:\n"
        "   - NOT_SUITABLE for: CVEs/security vulnerabilities, auth/crypto architecture, secrets handling, broad refactoring across many call sites (e.g. converting entire dialects or symbolic vocabularies), architectural redesigns, or high-risk infrastructure.\n"
        "   - SUITABLE only if approachable for a first-time contributor with zero architectural risk.\n"
        "12. PUBLICATION DECISION: Set 'publication_decision' as PUBLISH | REJECT | REVIEW_REQUIRED:\n"
        "   - Set PUBLISH ONLY IF: availability == AVAILABLE AND beginner_suitability == SUITABLE AND difficulty_tier in [BEGINNER, BEGINNER_PLUS] AND evidence_sufficiency == SUFFICIENT.\n"
        "   - Set REJECT if NOT_AVAILABLE, NOT_SUITABLE, ADVANCED, INTERMEDIATE, security/CVE, broad refactor, or maintainer restriction.\n"
        "   - Set REVIEW_REQUIRED if UNCERTAIN. Provide concise 'publication_reason'."
    )
    return prompt


def format_planning_prompt(evidence: EvidencePackage, investigation: Any) -> str:
    """Formats the investigation findings and repository guide into an evidence-first prompt for Phase 2 Planning."""
    locations_summary = []
    relevant_locations = getattr(investigation, "relevant_locations", []) or []
    for loc in relevant_locations:
        fp = getattr(loc, "file_path", "")
        sym = f" -> {getattr(loc, 'symbol_name', '')}" if getattr(loc, "symbol_name", None) else ""
        role = getattr(loc, "role", "Relevant Code")
        locations_summary.append(f"- {fp}{sym}: {role}")

    locs_text = "\n".join(locations_summary) if locations_summary else "Target locations identified in investigation."
    test_files = getattr(investigation, "relevant_test_files", []) or []
    tests_text = ", ".join(test_files) if test_files else "Existing test suite"

    summary = getattr(investigation, "summary", "")
    current_behavior = getattr(investigation, "current_behavior", "Current behavior described in issue.")
    expected_behavior = getattr(investigation, "expected_behavior", "Expected behavior specified.")
    why_it_happens = getattr(investigation, "why_it_happens", "")

    prompt = (
        f"You are a Senior Open-Source Maintainer creating an actionable contribution plan for '{evidence.issue.repo_full_name} #{evidence.issue.github_issue_number}'.\n\n"
        "=== INVESTIGATION FINDINGS ===\n"
        f"Problem Summary: {summary}\n"
        f"Current Behavior: {current_behavior}\n"
        f"Expected Behavior: {expected_behavior}\n"
        f"Root Cause Analysis: {why_it_happens}\n"
        f"Verified Target Locations:\n{locs_text}\n"
        f"Relevant Test Files: {tests_text}\n\n"
        "=== REPOSITORY TESTING & TOOLING ===\n"
        f"Primary Language: {evidence.repository.primary_language}\n"
        f"Verified Test Command: {evidence.repository.test_command} (Source: {evidence.repository.test_command_source})\n"
        f"Verified Lint Command: {evidence.repository.lint_command or 'NOT_VERIFIED'}\n\n"
        "=== STRICT PLANNING INSTRUCTIONS ===\n"
        "1. Define the 'minimal_change_area': Identify the smallest plausible modification required to resolve the issue safely without regressions.\n"
        "2. Create 3 to 5 concrete, ordered 'step_by_step_plan' items:\n"
        "   - Each step must reference exact verified symbols and file paths (e.g. 'Inspect symbol X in file Y and verify...').\n"
        "   - Step 1 must be inspection of the verified control flow.\n"
        "   - Middle steps must specify the focused implementation direction.\n"
        "   - Final steps must specify adding/updating the regression test and running the verified test command.\n"
        "   - Do NOT produce generic placeholder steps like 'Modify the code'.\n"
        "3. Provide a concrete 'regression_test_strategy' explaining what assertions are needed and how to cover the fix.\n"
        "4. Output the exact repository test command in 'suggested_test_command'."
    )
    return prompt


def format_grounded_prompt(
    repo_name: str,
    issue_title: str,
    issue_body: str,
    retrieved_chunks: List[Dict[str, Any]]
) -> str:
    """Backward-compatible prompt formatter for legacy callers/tests."""
    formatted_context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        header = chunk.get("contextual_header") or f"[File: {chunk.get('file_path')}]"
        content = chunk.get("content", "").strip()[:1000]
        info_cls = chunk.get("info_class", "SOURCE_CODE")
        block = f"--- EVIDENCE BLOCK {idx} [{info_cls}] ---\n{header}\n{content}\n"
        formatted_context_blocks.append(block)

    context_str = "\n".join(formatted_context_blocks)
    truncated_body = (issue_body or "").strip()[:1500]

    prompt = (
        f"You are analyzing GitHub Issue #{issue_title} for repository '{repo_name}'.\n\n"
        f"ISSUE TITLE: {issue_title}\n"
        f"ISSUE BODY: {truncated_body or 'No body description provided.'}\n\n"
        f"RELEVANT CODEBASE EVIDENCE CHUNKS:\n"
        f"{context_str}\n\n"
        "STRICT GROUNDING INSTRUCTIONS:\n"
        "1. Base your root cause analysis and solution steps ONLY on the codebase evidence blocks provided above.\n"
        "2. Do NOT invent or hallucinate non-existent file paths, class names, or function names.\n"
        "3. Include exact relative file paths in relevant_locations matching the evidence blocks.\n"
        "4. Provide beginner-friendly, step-by-step guided instructions.\n"
    )
    return prompt


def generate_issue_explanation(
    repo_name: str,
    issue_title: str,
    issue_body: str = "",
    retrieved_chunks: List[Dict[str, Any]] = None,
    evidence_package: Optional[EvidencePackage] = None,
    provider: Optional[BaseLLMProvider] = None,
) -> IssueExplanation:
    """
    Generates a multi-phase verified IssueExplanation.
    
    1. Short-circuits with INSUFFICIENT_EVIDENCE if context < 100 tokens.
    2. Phase 1: Executes Code Investigation & Control Flow Reasoning.
    3. Phase 2: Executes Grounded Planning & Minimal Change Strategy.
    4. Programmatic Grounding Verification: Prunes unverified citations.
    """
    raw_chunks = retrieved_chunks or []
    if evidence_package:
        raw_chunks = [
            {
                "chunk_id": c.chunk_id,
                "file_path": c.file_path,
                "symbol_name": c.symbol_name,
                "qualified_symbol_name": c.qualified_symbol_name,
                "symbol_type": c.symbol_type,
                "info_class": c.info_class,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "content": c.content,
                "contextual_header": c.contextual_header,
                "commit_sha": c.commit_sha,
                "retrieval_method": c.retrieval_method,
            }
            for c in evidence_package.code_evidence
        ] + [
            {
                "chunk_id": t.chunk_id,
                "file_path": t.file_path,
                "symbol_name": t.test_function_name,
                "qualified_symbol_name": t.test_function_name,
                "symbol_type": "test_function",
                "info_class": "TESTS",
                "start_line": t.start_line,
                "end_line": t.end_line,
                "content": t.content,
                "contextual_header": t.contextual_header,
                "commit_sha": "",
                "retrieval_method": "hybrid_rrf",
            }
            for t in evidence_package.test_evidence
        ]

    # 1. Evidence Short-Circuit Check
    if GroundingVerifier.is_evidence_insufficient(raw_chunks, min_token_threshold=100):
        return GroundingVerifier.build_insufficient_evidence_response(
            reason="Retrieved repository context contains insufficient evidence (<100 tokens)."
        )

    # 2. Construct EvidencePackage if not supplied directly
    if not evidence_package:
        from app.schemas.evidence import (
            IssueEvidence,
            StatusEvidence,
            RepositoryEvidence,
            CodeEvidenceItem,
            TestEvidenceItem,
            DiscussionEvidence,
        )
        code_items = [
            CodeEvidenceItem(
                chunk_id=c.get("chunk_id", f"c_{i}"),
                file_path=c.get("file_path", ""),
                symbol_name=c.get("symbol_name"),
                qualified_symbol_name=c.get("qualified_symbol_name"),
                symbol_type=c.get("symbol_type"),
                info_class=c.get("info_class", "SOURCE_CODE"),
                start_line=c.get("start_line", 1),
                end_line=c.get("end_line", 1),
                content=c.get("content", ""),
                contextual_header=c.get("contextual_header")
            )
            for i, c in enumerate(raw_chunks) if "test" not in c.get("file_path", "").lower()
        ]
        test_items = [
            TestEvidenceItem(
                chunk_id=c.get("chunk_id", f"t_{i}"),
                file_path=c.get("file_path", ""),
                test_function_name=c.get("symbol_name"),
                start_line=c.get("start_line", 1),
                end_line=c.get("end_line", 1),
                content=c.get("content", ""),
                contextual_header=c.get("contextual_header")
            )
            for i, c in enumerate(raw_chunks) if "test" in c.get("file_path", "").lower()
        ]
        evidence_package = EvidencePackage(
            issue=IssueEvidence(
                repo_full_name=repo_name,
                github_issue_number=1,
                title=issue_title,
                body=issue_body or "",
                reporter_username="community_contributor",
                html_url=f"https://github.com/{repo_name}/issues/1"
            ),
            status=StatusEvidence(
                availability_status="CHECK_DISCUSSION",
                confidence="HIGH",
                last_verified_at="2026-08-14T00:00:00Z"
            ),
            repository=RepositoryEvidence(
                repo_full_name=repo_name,
                primary_language="Python",
                current_commit_sha="HEAD"
            ),
            code_evidence=code_items,
            test_evidence=test_items,
            discussion=DiscussionEvidence(),
            package_timestamp="2026-08-14T00:00:00Z"
        )

    # 3. Resolve Active LLM Provider
    active_provider = provider or LLMProviderFactory.get_provider()

    # 4. Phase 1: Code Investigation & Control Flow Reasoning
    investigation_prompt = format_investigation_prompt(evidence_package)
    investigation_res: Optional[LLMInvestigationPayload] = None
    
    try:
        investigation_res = active_provider.generate_structured(
            investigation_prompt,
            LLMInvestigationPayload
        )
    except Exception as e:
        # Attempt graceful context reduction retry
        try:
            from app.pipeline.evidence_builder import EvidenceBuilder
            reduced_evidence = EvidenceBuilder.apply_graceful_context_reduction(
                evidence_package,
                target_token_budget=4000
            )
            reduced_prompt = format_investigation_prompt(reduced_evidence)
            investigation_res = active_provider.generate_structured(
                reduced_prompt,
                LLMInvestigationPayload
            )
        except Exception as retry_err:
            return GroundingVerifier.build_insufficient_evidence_response(
                reason=f"LLM investigation could not complete with available evidence: {retry_err}"
            )

    if not investigation_res:
        return GroundingVerifier.build_insufficient_evidence_response(
            reason="Investigation produced no valid structured response."
        )

    # 5. Phase 2: Grounded Planning & Minimal Change Strategy
    planning_prompt = format_planning_prompt(evidence_package, investigation_res)
    plan_res: Optional[LLMPlanPayload] = None
    try:
        plan_res = active_provider.generate_structured(
            planning_prompt,
            LLMPlanPayload
        )
    except Exception as e:
        # Attempt reduced planning prompt
        try:
            from app.pipeline.evidence_builder import EvidenceBuilder
            reduced_evidence = EvidenceBuilder.apply_graceful_context_reduction(
                evidence_package,
                target_token_budget=4000
            )
            reduced_plan_prompt = format_planning_prompt(reduced_evidence, investigation_res)
            plan_res = active_provider.generate_structured(
                reduced_plan_prompt,
                LLMPlanPayload
            )
        except Exception:
            plan_res = None

    # 6. Combine Multi-Phase Results into IssueExplanation
    plan_steps = getattr(plan_res, "step_by_step_plan", None) or getattr(investigation_res, "step_by_step_plan", [])
    raw_concepts = getattr(investigation_res, "structured_concepts", []) or []
    prereqs = [c.concept_name for c in raw_concepts if hasattr(c, "concept_name")] or getattr(investigation_res, "prerequisite_concepts", ["Repository Architecture"])

    raw_explanation = IssueExplanation(
        status="SUCCESS",
        summary=getattr(investigation_res, "summary", issue_title),
        why_it_happens=getattr(investigation_res, "why_it_happens", "Root cause identified in target code."),
        prerequisite_concepts=prereqs,
        structured_concepts=raw_concepts,
        step_by_step_plan=plan_steps,
        relevant_locations=getattr(investigation_res, "relevant_locations", []),
        common_pitfalls=getattr(investigation_res, "common_pitfalls", []),
        difficulty_tier=getattr(investigation_res, "difficulty_tier", "BEGINNER"),
        difficulty_reasoning=getattr(investigation_res, "difficulty_reasoning", ""),
        availability=getattr(investigation_res, "availability", "AVAILABLE"),
        availability_reasoning=getattr(investigation_res, "availability_reasoning", ""),
        beginner_suitability_decision=getattr(investigation_res, "beginner_suitability", "SUITABLE"),
        evidence_sufficiency=getattr(investigation_res, "evidence_sufficiency", "SUFFICIENT"),
        publication_decision=getattr(investigation_res, "publication_decision", "PUBLISH"),
        publication_reason=getattr(investigation_res, "publication_reason", ""),
        llm_provider=getattr(active_provider, "provider_name", "google"),
        llm_model=getattr(active_provider, "model_name", "gemini-3.6-flash")
    )

    # 7. Programmatic Grounding Verification & Citation Sanitization
    verifier = GroundingVerifier(raw_chunks)
    validated_explanation = verifier.verify_and_sanitize(raw_explanation)

    return validated_explanation
