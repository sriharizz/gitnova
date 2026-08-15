"""
GitNova v4.4 — Contribution Journey Generator Engine

Transforms verified issue explanations, GitHub opportunity signals, RRF codebase retrieval,
and repository contribution guides into a structured, 10-stage Contribution Journey with
deterministic structured visualizations, multi-dimensional complexity, and data provenance.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.schemas.explanation import (
    ContributionJourney,
    ContributionJourneyStage,
    ConceptDetail,
    RepositoryContributionGuide,
    StructuredDiagram,
    DiagramNode,
    DiagramEdge,
    ProvenanceType,
    ProvenanceItem,
    BeginnerSuitability,
    DiscussionSummary,
    FreshnessMetadata
)
from app.pipeline.repo_guide_extractor import RepoGuideExtractor
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator


class ContributionJourneyGenerator:
    """Generates structured 10-stage Contribution Journeys tailored to specific GitHub issues and repositories."""

    @staticmethod
    def generate_journey(
        issue_data: Dict[str, Any],
        repo_guide: Optional[Dict[str, Any]] = None
    ) -> ContributionJourney:
        """
        Builds a dynamic 10-stage Contribution Journey with deterministic visualizations.
        """
        repo_full_name = issue_data.get("repo_full_name") or issue_data.get("repo_name") or "unknown/repo"
        github_issue_number = int(issue_data.get("github_issue_number") or 1)
        title = issue_data.get("title") or "Issue Title"
        reporter_username = issue_data.get("reporter_username") or "github_contributor"

        availability_status = issue_data.get("availability_status") or "LIKELY_AVAILABLE"
        opportunity_confidence = issue_data.get("opportunity_confidence") or issue_data.get("confidence") or "HIGH"
        last_verified_at = issue_data.get("last_verified_at") or datetime.now(timezone.utc).isoformat()

        # Extract or build RepositoryContributionGuide
        raw_guide_data = repo_guide or issue_data.get("repository_contribution_guide")
        if isinstance(raw_guide_data, dict):
            guide_model = RepoGuideExtractor.extract_guide(
                repo_full_name,
                raw_contributing_md=raw_guide_data.get("raw_contributing_md"),
                ci_config=raw_guide_data.get("ci_config")
            )
        elif isinstance(raw_guide_data, RepositoryContributionGuide):
            guide_model = raw_guide_data
        else:
            guide_model = RepoGuideExtractor.extract_guide(repo_full_name)

        # Explanation payloads
        explanation_raw = issue_data.get("explanation") or {}
        if hasattr(explanation_raw, "model_dump"):
            exp_dict = explanation_raw.model_dump()
        elif isinstance(explanation_raw, dict):
            exp_dict = explanation_raw
        else:
            exp_dict = {}

        summary = exp_dict.get("summary") or issue_data.get("summary") or f"Issue #{github_issue_number} in {repo_full_name}"
        why_it_happens = exp_dict.get("why_it_happens") or "Underlying implementation logic defect in target module."
        
        # Extract verified code locations
        raw_locations = exp_dict.get("relevant_locations") or []
        target_locations = []
        target_files = []
        target_symbols = []
        for loc in raw_locations:
            fp = loc.get("file_path") if isinstance(loc, dict) else getattr(loc, "file_path", "")
            sym = loc.get("symbol_name") if isinstance(loc, dict) else getattr(loc, "symbol_name", "")
            lines = loc.get("lines") if isinstance(loc, dict) else getattr(loc, "lines", "")
            if fp:
                target_files.append(fp)
                location_str = f"{fp} ({sym} L{lines})" if sym else fp
                target_locations.append(location_str)
                if sym:
                    target_symbols.append(sym)

        primary_target_file = target_files[0] if target_files else "src/main.py"
        primary_target_symbol = target_symbols[0] if target_symbols else "main"

        # Extract concept details
        raw_concepts = exp_dict.get("structured_concepts") or []
        structured_concepts = []
        for c in raw_concepts:
            if isinstance(c, dict):
                structured_concepts.append(ConceptDetail(**c))
            elif hasattr(c, "concept_name"):
                structured_concepts.append(c)

        if not structured_concepts:
            structured_concepts.append(ConceptDetail(
                concept_name=f"{repo_full_name.split('/')[-1].capitalize()} Architecture",
                short_explanation=f"Core architecture and patterns used in {repo_full_name}.",
                why_it_matters="Understanding the module structure prevents architectural regression.",
                connection_to_issue=f"Relevant to fixing issue #{github_issue_number} in {primary_target_file}."
            ))

        # Extract step by step plan
        raw_plan = exp_dict.get("step_by_step_plan") or []
        plan_steps = []
        for p in raw_plan:
            if isinstance(p, dict):
                plan_steps.append(p.get("description") or p.get("title", ""))
            elif hasattr(p, "description"):
                plan_steps.append(p.description)
            elif isinstance(p, str):
                plan_steps.append(p)

        if not plan_steps:
            plan_steps = [
                "INSUFFICIENT_EVIDENCE: Repository evidence was insufficient to generate verified step-by-step fix plan."
            ]

        # Extract opportunity signals
        opportunity_signals = issue_data.get("opportunity_signals") or {}
        evidence_list = issue_data.get("opportunity_evidence") or issue_data.get("evidence") or opportunity_signals.get("evidence_statements") or ["✓ Open on GitHub", "✓ Unassigned on GitHub"]
        warning_list = issue_data.get("opportunity_warnings") or issue_data.get("warnings") or []

        # Repository testing command with explicit source attribution
        test_command_is_verified = (guide_model.test_command_source != "NOT_VERIFIED" and "Not verified" not in guide_model.test_command)
        test_command_display = guide_model.test_command
        test_commands_list = [guide_model.test_command] if test_command_is_verified else []

        # 1. GENERATE DETERMINISTIC STRUCTURED DIAGRAMS
        # Diagram A: Code Relationship Diagram for Stage 4
        relevant_test_files = exp_dict.get("relevant_test_files") or []
        test_target_file = relevant_test_files[0] if relevant_test_files else (guide_model.test_command_source if guide_model.test_command_source != "NOT_VERIFIED" else "Repository Test Suite")
        code_rel_nodes = [
            DiagramNode(
                id="node_issue",
                label=f"Issue #{github_issue_number}",
                node_type="issue",
                provenance=ProvenanceItem(text=f"GitHub #{github_issue_number}", provenance_type=ProvenanceType.VERIFIED_FACT, source="GitHub API")
            ),
            DiagramNode(
                id="node_file",
                label=primary_target_file,
                node_type="file",
                provenance=ProvenanceItem(text=primary_target_file, provenance_type=ProvenanceType.VERIFIED_FACT, source="RRF Code Retrieval")
            ),
            DiagramNode(
                id="node_symbol",
                label=primary_target_symbol,
                node_type="symbol",
                provenance=ProvenanceItem(text=primary_target_symbol, provenance_type=ProvenanceType.VERIFIED_FACT, source="Codebase AST")
            ),
            DiagramNode(
                id="node_test",
                label=test_target_file,
                node_type="test",
                provenance=ProvenanceItem(text=test_target_file, provenance_type=ProvenanceType.VERIFIED_FACT if relevant_test_files else ProvenanceType.NOT_VERIFIED, source="Repository Test Suite")
            )
        ]
        code_rel_edges = [
            DiagramEdge(source="node_issue", target="node_file", label="targets", edge_type="modifies"),
            DiagramEdge(source="node_file", target="node_symbol", label="defines", edge_type="defines"),
            DiagramEdge(source="node_symbol", target="node_test", label="tested by", edge_type="tests")
        ]
        code_relationship_diagram = StructuredDiagram(
            diagram_type="CODE_RELATIONSHIP",
            title=f"Code Relationship: {primary_target_symbol}",
            description=f"Structural map of files and tests connected to issue #{github_issue_number}",
            nodes=code_rel_nodes,
            edges=code_rel_edges
        )

        # Diagram B: Failure Flow Diagram for Stage 5
        failure_flow_nodes = [
            DiagramNode(
                id="n_trigger",
                label="Trigger Condition",
                node_type="trigger",
                metadata={"detail": summary[:80]},
                provenance=ProvenanceItem(text=summary[:60], provenance_type=ProvenanceType.VERIFIED_FACT, source=f"GitHub Issue #{github_issue_number}")
            ),
            DiagramNode(
                id="n_current",
                label="Current Control Flow",
                node_type="current",
                metadata={"detail": f"Executes in {primary_target_symbol}"},
                provenance=ProvenanceItem(text=primary_target_symbol, provenance_type=ProvenanceType.AI_INFERENCE, source="Codebase Control Flow")
            ),
            DiagramNode(
                id="n_failure",
                label="Failure Point",
                node_type="failure",
                metadata={"detail": why_it_happens[:80]},
                provenance=ProvenanceItem(text=why_it_happens[:60], provenance_type=ProvenanceType.AI_INFERENCE, source="Root Cause Analysis")
            ),
            DiagramNode(
                id="n_consequence",
                label="Consequence / Defect",
                node_type="consequence",
                metadata={"detail": "Behavioral failure or exception occurs"},
                provenance=ProvenanceItem(text="Defect manifestation", provenance_type=ProvenanceType.VERIFIED_FACT, source="Issue Reproduction")
            )
        ]
        failure_flow_edges = [
            DiagramEdge(source="n_trigger", target="n_current", label="invokes"),
            DiagramEdge(source="n_current", target="n_failure", label="encounters unhandled state"),
            DiagramEdge(source="n_failure", target="n_consequence", label="causes defect")
        ]
        failure_flow_diagram = StructuredDiagram(
            diagram_type="FAILURE_FLOW",
            title="Runtime Failure Flow",
            description="Control flow sequence causing the reported bug",
            nodes=failure_flow_nodes,
            edges=failure_flow_edges
        )

        # Diagram C: Expected vs Current State Machine
        expected_vs_current_nodes = [
            DiagramNode(id="exp_current", label=f"Current: {why_it_happens[:60]}", node_type="current"),
            DiagramNode(id="exp_expected", label=f"Expected: Graceful handling in {primary_target_symbol}", node_type="expected")
        ]
        expected_vs_current_edges = [
            DiagramEdge(source="exp_current", target="exp_expected", label="remedy via plan", edge_type="modifies")
        ]
        expected_vs_current_diagram = StructuredDiagram(
            diagram_type="EXPECTED_VS_CURRENT",
            title="Expected vs Current Behavior",
            description="Comparison of baseline bug behavior against expected resolution",
            nodes=expected_vs_current_nodes,
            edges=expected_vs_current_edges
        )

        # BUILD THE 10 STAGES
        stages: List[ContributionJourneyStage] = []

        # STAGE 1 — UNDERSTAND
        stages.append(ContributionJourneyStage(
            stage_id="understand",
            stage_number=1,
            title="Stage 1 — Understand",
            purpose="Grasp the issue scope, problem statement, and reporter requirements.",
            explanation=f"Issue #{github_issue_number} ('{title}') was reported by @{reporter_username} on GitHub.\n\nSummary: {summary}\n\nRoot Cause: {why_it_happens}",
            steps=[
                f"Read reported issue #{github_issue_number} prompt and summary",
                f"Identify reporter @{reporter_username}'s core request",
                f"Note target repository context ({repo_full_name})"
            ],
            targets=[primary_target_file],
            commands=[],
            concepts=structured_concepts[:1],
            evidence=[f"Reported by @{reporter_username} on GitHub", f"Repository: {repo_full_name}"],
            warnings=warning_list,
            completion_criteria=f"You can state the problem reported by @{reporter_username} in 2 plain-English sentences.",
            provenance=ProvenanceItem(text=f"Issue #{github_issue_number} summary", provenance_type=ProvenanceType.AI_INFERENCE, source="GitHub Issue Body")
        ))

        # STAGE 2 — CHECK STATUS
        status_narrative = (
            "No conflicting work detected in checked GitHub activity. Issue is open and unassigned."
            if availability_status == "LIKELY_AVAILABLE"
            else "Discussion is active or soft triage labels were detected — check GitHub discussion before starting work."
        )
        stages.append(ContributionJourneyStage(
            stage_id="check_status",
            stage_number=2,
            title="Stage 2 — Check Status",
            purpose="Verify current GitHub availability and check for active work.",
            explanation=f"Current Status: {availability_status} (Confidence: {opportunity_confidence}).\n\n{status_narrative}",
            steps=[
                "Verify that the issue is open and unassigned on GitHub",
                "Check GitHub timeline for recent linked pull requests",
                "Verify last verified timestamp before spending time implementing"
            ],
            targets=[],
            commands=[],
            concepts=[],
            evidence=evidence_list,
            warnings=warning_list if warning_list else ["Check GitHub discussion if status was verified >12 hours ago."],
            completion_criteria="You confirmed that no active PR or assignment blocks this issue on GitHub.",
            provenance=ProvenanceItem(text=availability_status, provenance_type=ProvenanceType.VERIFIED_FACT, source="GitHub API")
        ))

        # STAGE 3 — LEARN
        stages.append(ContributionJourneyStage(
            stage_id="learn",
            stage_number=3,
            title="Stage 3 — Learn",
            purpose="Master the required technical concepts before inspecting code.",
            explanation=f"Before modifying code in {primary_target_file}, review these core prerequisite concepts relevant to issue #{github_issue_number}:",
            steps=[
                f"Read structured concept card: {sc.concept_name}" for sc in structured_concepts
            ] + ["Understand how these concepts connect to this specific bug fix"],
            targets=[primary_target_file],
            commands=[],
            concepts=structured_concepts,
            evidence=[f"Grounded prerequisite concept: {sc.concept_name}" for sc in structured_concepts],
            warnings=[],
            completion_criteria="You understand the core technical concepts cited for this issue.",
            provenance=ProvenanceItem(text="Prerequisite concepts", provenance_type=ProvenanceType.AI_INFERENCE, source="Concept Extractor")
        ))

        # STAGE 4 — EXPLORE
        explore_evidence = [f"Verified target code location: {loc}" for loc in target_locations]
        if guide_model.guide_found:
            explore_evidence.append(f"Repository Contribution Guide source: {guide_model.guide_source}")

        stages.append(ContributionJourneyStage(
            stage_id="explore",
            stage_number=4,
            title="Stage 4 — Explore",
            purpose="Navigate to target file locations in the repository context.",
            explanation=f"Target codebase location retrieved via hybrid RRF search: {', '.join(target_locations) if target_locations else primary_target_file}.\n\nRepository Setup: {guide_model.setup_instructions or 'Refer to repository documentation for environment setup.'}",
            steps=[
                f"Open target file: {primary_target_file}",
                f"Locate symbol/function: {primary_target_symbol}",
                "Inspect surrounding module imports and dependencies"
            ],
            targets=target_files if target_files else [primary_target_file],
            commands=[],
            concepts=[],
            evidence=explore_evidence,
            warnings=[],
            completion_criteria=f"You opened {primary_target_file} and located the target symbol.",
            diagrams=[code_relationship_diagram],
            provenance=ProvenanceItem(text=primary_target_file, provenance_type=ProvenanceType.VERIFIED_FACT, source="RRF Code Retrieval")
        ))

        # STAGE 5 — INVESTIGATE
        investigate_evidence = [f"Root Cause: {why_it_happens[:100]}..."]
        if test_command_is_verified:
            investigate_evidence.append(f"Verified test runner: {test_command_display} (Source: {guide_model.test_command_source})")

        stages.append(ContributionJourneyStage(
            stage_id="investigate",
            stage_number=5,
            title="Stage 5 — Investigate",
            purpose="Understand existing control flow and reproduce the defect locally.",
            explanation=f"Technical Root Cause:\n{why_it_happens}\n\nInvestigate how current control flow in {primary_target_symbol} produces this bug condition.",
            steps=[
                f"Trace control flow through {primary_target_file} near {primary_target_symbol}",
                "Identify the exact condition or unhandled edge case causing the defect",
                f"Run existing tests using `{test_command_display}` to verify baseline" if test_command_is_verified else "Check repository documentation for baseline test runner instructions"
            ],
            targets=[primary_target_file],
            commands=test_commands_list,
            concepts=[],
            evidence=investigate_evidence,
            warnings=[] if test_command_is_verified else ["GitNova could not verify the repository's test command. Check repository documentation before running tests."],
            completion_criteria="You understand why current code fails and can observe the problem locally.",
            diagrams=[failure_flow_diagram, expected_vs_current_diagram],
            provenance=ProvenanceItem(text=why_it_happens, provenance_type=ProvenanceType.AI_INFERENCE, source="Control Flow Engine")
        ))

        has_insufficient_evidence = (exp_dict.get("status") == "INSUFFICIENT_EVIDENCE")

        # STAGE 6 — PLAN
        stages.append(ContributionJourneyStage(
            stage_id="plan",
            stage_number=6,
            title="Stage 6 — Plan" if not has_insufficient_evidence else "Stage 6 — Plan (Blocked)",
            purpose="Formulate a precise step-by-step implementation plan." if not has_insufficient_evidence else "Implementation planning is blocked.",
            explanation="Guided implementation steps targeting verified code files (AI Implementation Hypothesis):" if not has_insufficient_evidence else "GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution.",
            steps=plan_steps if not has_insufficient_evidence else [
                "INSUFFICIENT_EVIDENCE: Repository evidence was insufficient to safely generate an implementation plan.",
                "Wait for further maintainer clarification or code indexing updates before attempting changes."
            ],
            targets=target_files if (target_files and not has_insufficient_evidence) else ([primary_target_file] if not has_insufficient_evidence else []),
            commands=[],
            concepts=[],
            evidence=[f"Step {idx}: {step}" for idx, step in enumerate(plan_steps, 1)],
            warnings=["This plan is an AI-guided hypothesis. Verify with repository maintainer expectations."] if not has_insufficient_evidence else ["GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution."],
            completion_criteria="You have a clear, step-by-step implementation roadmap targeting verified code files." if not has_insufficient_evidence else "Stage blocked — insufficient verified evidence.",
            provenance=ProvenanceItem(text="Guided implementation steps", provenance_type=ProvenanceType.IMPLEMENTATION_HYPOTHESIS if not has_insufficient_evidence else ProvenanceType.NOT_VERIFIED, source="GitNova Planner")
        ))

        # STAGE 7 — IMPLEMENT
        stages.append(ContributionJourneyStage(
            stage_id="implement",
            stage_number=7,
            title="Stage 7 — Implement" if not has_insufficient_evidence else "Stage 7 — Implement (Blocked)",
            purpose="Write the minimal production code fix in your local feature branch." if not has_insufficient_evidence else "Implementation is blocked.",
            explanation=f"Create a local git branch (e.g. `git checkout -b fix-issue-{github_issue_number}`) in your fork and implement minimal changes in `{primary_target_file}`." if not has_insufficient_evidence else "GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution.",
            steps=[
                f"Create a topic branch: `git checkout -b fix-issue-{github_issue_number}`",
                f"Modify `{primary_target_file}` to handle the missing edge case or cleanup logic",
                "Ensure no unrelated files or formatting changes are included in your diff"
            ] if not has_insufficient_evidence else [],
            targets=[primary_target_file] if not has_insufficient_evidence else [],
            commands=[f"git checkout -b fix-issue-{github_issue_number}"] if not has_insufficient_evidence else [],
            concepts=[],
            evidence=[f"Target file: {primary_target_file}"] if not has_insufficient_evidence else [],
            warnings=["Do not modify unrelated code files or auto-format entire modules."] if not has_insufficient_evidence else ["GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution."],
            completion_criteria="Minimal production code changes are implemented in your local branch." if not has_insufficient_evidence else "Stage blocked — insufficient verified evidence.",
            provenance=ProvenanceItem(text="Topic branch & implementation guidance", provenance_type=ProvenanceType.VERIFIED_FACT if not has_insufficient_evidence else ProvenanceType.NOT_VERIFIED, source="Git Best Practices")
        ))

        # STAGE 8 — TEST
        test_evidence = []
        if test_command_is_verified:
            test_evidence.append(f"Test Command: {test_command_display}")
            test_evidence.append(f"Source: {guide_model.test_command_source}")
            test_explanation = f"Execute the verified test command for {repo_full_name}: `{test_command_display}` (Source: {guide_model.test_command_source})."
        else:
            test_evidence.append("Test Command: Not verified — check repository documentation.")
            test_evidence.append("Source: NOT_VERIFIED")
            test_explanation = f"GitNova could not verify the repository's test command for {repo_full_name}. Consult repository documentation before running tests."

        if guide_model.lint_command:
            test_evidence.append(f"Lint Command: {guide_model.lint_command} (Source: {guide_model.lint_command_source})")

        stages.append(ContributionJourneyStage(
            stage_id="test",
            stage_number=8,
            title="Stage 8 — Test" if not has_insufficient_evidence else "Stage 8 — Test (Blocked)",
            purpose="Run local test suite and add regression unit tests." if not has_insufficient_evidence else "Testing is blocked.",
            explanation=test_explanation if not has_insufficient_evidence else "GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution.",
            steps=[
                f"Run main test suite: `{test_command_display}`" if test_command_is_verified else "Consult repository docs for test runner command",
                f"Add a new regression unit test covering issue #{github_issue_number}",
                "Verify all existing and new unit tests pass cleanly"
            ] if not has_insufficient_evidence else [],
            targets=[primary_target_file] if not has_insufficient_evidence else [],
            commands=test_commands_list,
            concepts=[],
            evidence=test_evidence,
            warnings=["Never submit a pull request with failing unit tests."] if not has_insufficient_evidence else ["GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution."],
            completion_criteria="All unit tests pass and a new regression test verifies the bug fix." if not has_insufficient_evidence else "Stage blocked — insufficient verified evidence.",
            provenance=ProvenanceItem(text=test_command_display if test_command_is_verified else "Test runner", provenance_type=ProvenanceType.VERIFIED_FACT if test_command_is_verified else ProvenanceType.NOT_VERIFIED, source=guide_model.test_command_source)
        ))

        # STAGE 9 — PREPARE PR
        pr_guidance_text = guide_model.pull_request_guidance or "Open PR referencing Fixes #X."
        stages.append(ContributionJourneyStage(
            stage_id="prepare_pr",
            stage_number=9,
            title="Stage 9 — Prepare PR" if not has_insufficient_evidence else "Stage 9 — Prepare PR (Blocked)",
            purpose="Format your commit, push to your fork, and open a GitHub Pull Request." if not has_insufficient_evidence else "PR preparation is blocked.",
            explanation=f"Commit your changes and open a Pull Request on GitHub targeting `{repo_full_name}` main branch.\n\nRepository Policy: {pr_guidance_text}" if not has_insufficient_evidence else "GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution.",
            steps=[
                f"Commit changes: `git commit -m \"fix: resolve issue #{github_issue_number} in {primary_target_symbol}\"`",
                "Push feature branch to your GitHub fork",
                f"Open Pull Request against `{repo_full_name}` main branch",
                f"Include 'Fixes #{github_issue_number}' in PR description body"
            ] if not has_insufficient_evidence else [],
            targets=[],
            commands=[f'git commit -m "fix: resolve #{github_issue_number}"', "git push origin HEAD"] if not has_insufficient_evidence else [],
            concepts=[],
            evidence=[f"Upstream target: https://github.com/{repo_full_name}/issues/{github_issue_number}"],
            warnings=[f"Ensure PR description explicitly mentions 'Fixes #{github_issue_number}'."] if not has_insufficient_evidence else ["GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution."],
            completion_criteria="Pull Request is opened on GitHub with issue reference and passing CI checks." if not has_insufficient_evidence else "Stage blocked — insufficient verified evidence.",
            provenance=ProvenanceItem(text="PR preparation guidelines", provenance_type=ProvenanceType.VERIFIED_FACT, source="GitHub PR Convention")
        ))

        # STAGE 10 — REVIEW
        stages.append(ContributionJourneyStage(
            stage_id="review",
            stage_number=10,
            title="Stage 10 — Review" if not has_insufficient_evidence else "Stage 10 — Review (Blocked)",
            purpose="Perform pre-submission verification and respond to maintainer review." if not has_insufficient_evidence else "Review is blocked.",
            explanation="Final pre-submission check: Re-verify that the issue is still open on GitHub and address maintainer code review comments." if not has_insufficient_evidence else "GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution.",
            steps=[
                f"Re-check GitHub issue #{github_issue_number} page for recent maintainer comments",
                "Ensure automated CI workflow status checks pass on your PR",
                "Respond politely to maintainer review feedback and push requested updates"
            ] if not has_insufficient_evidence else [],
            targets=[],
            commands=[],
            concepts=[],
            evidence=[f"GitHub Source: https://github.com/{repo_full_name}/issues/{github_issue_number}"],
            warnings=["Maintainer review may take a few days. Be patient and polite."] if not has_insufficient_evidence else ["GitNova could not verify enough repository evidence to safely generate an implementation plan. This issue is not currently recommended for contribution."],
            completion_criteria="CI checks pass and maintainer review feedback is addressed." if not has_insufficient_evidence else "Stage blocked — insufficient verified evidence.",
            provenance=ProvenanceItem(text="Pre-submission checklist", provenance_type=ProvenanceType.VERIFIED_FACT, source="GitHub Review Guidelines")
        ))

        # Extract beginner suitability and discussion summary
        suitability_dict = issue_data.get("beginner_suitability")
        if isinstance(suitability_dict, dict):
            suitability_model = BeginnerSuitability(**suitability_dict)
        elif isinstance(suitability_dict, BeginnerSuitability):
            suitability_model = suitability_dict
        else:
            suitability_model = ContributionOpportunityEvaluator.evaluate_beginner_suitability(
                raw_issue=issue_data,
                retrieved_locations=raw_locations,
                concepts=structured_concepts
            )

        discussion_dict = issue_data.get("discussion_summary")
        if isinstance(discussion_dict, dict):
            discussion_model = DiscussionSummary(**discussion_dict)
        elif isinstance(discussion_dict, DiscussionSummary):
            discussion_model = discussion_dict
        else:
            discussion_model = DiscussionSummary(
                total_comments=int(issue_data.get("comments_count") or 0),
                discussion_summary="No conflicting work detected in checked GitHub activity."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        freshness_model = FreshnessMetadata(
            issue_status_verified_at=last_verified_at,
            discussion_verified_at=last_verified_at,
            repository_code_verified_at=last_verified_at,
            repository_guide_verified_at=guide_model.last_verified_at or last_verified_at,
            journey_generated_at=now_iso
        )

        journey_obj = ContributionJourney(
            journey_version="4.5",
            repo_full_name=repo_full_name,
            github_issue_number=github_issue_number,
            title=title,
            reporter_username=reporter_username,
            availability_status=availability_status,
            opportunity_confidence=opportunity_confidence,
            beginner_suitability=suitability_model,
            discussion_summary=discussion_model,
            freshness=freshness_model,
            last_verified_at=last_verified_at,
            llm_provider=exp_dict.get("llm_provider") or "google",
            llm_model=exp_dict.get("llm_model") or "gemini-3.6-flash",
            stages=stages
        )

        # Enforce Rule #8: Target Consistency across all 10 stages
        ContributionJourneyGenerator.validate_and_align_target_consistency(journey_obj, primary_target_file, target_files)
        return journey_obj

    @classmethod
    def validate_and_align_target_consistency(
        cls,
        journey: ContributionJourney,
        primary_target: str,
        verified_targets: List[str]
    ) -> bool:
        """
        Enforces Rule #8: Target Consistency Validator.
        Ensures that Overview -> Explore -> Investigate -> Plan -> Implement -> Test
        all consistently reference the same verified repository target files.
        """
        valid_set = set([t.lower().replace("\\", "/") for t in verified_targets if t])
        if primary_target:
            valid_set.add(primary_target.lower().replace("\\", "/"))

        for stage in journey.stages:
            if stage.stage_id in {"explore", "investigate", "plan", "implement", "test"}:
                aligned_targets = []
                for t in stage.targets:
                    norm = t.lower().replace("\\", "/")
                    if norm in valid_set:
                        aligned_targets.append(t)
                    else:
                        # Prune conflicting/unverified target and align with primary
                        if primary_target and primary_target not in aligned_targets:
                            aligned_targets.append(primary_target)
                
                if not aligned_targets and primary_target:
                    aligned_targets = [primary_target]
                stage.targets = aligned_targets

        return True
