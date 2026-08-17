"""
GitNova v4.4 — Grounded Issue Explanation & Contribution Intelligence Pydantic Schema

Structured output schema for beginner-friendly guided issue explanations,
multi-dimensional difficulty assessment, structured deterministic diagrams, and provenance.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class ProvenanceType(str, Enum):
    VERIFIED_FACT = "VERIFIED_FACT"
    MAINTAINER_INTENT = "MAINTAINER_INTENT"
    AI_INFERENCE = "AI_INFERENCE"
    IMPLEMENTATION_HYPOTHESIS = "IMPLEMENTATION_HYPOTHESIS"
    NOT_VERIFIED = "NOT_VERIFIED"


class ProvenanceItem(BaseModel):
    """Provenance tracking record for evidence-backed statements."""
    text: str = Field(default="", description="The underlying statement or entity")
    provenance_type: ProvenanceType = Field(default=ProvenanceType.VERIFIED_FACT)
    source: Optional[str] = Field(default="Codebase Evidence", description="Direct source (e.g. GitHub API, CONTRIBUTING.md, RRF retrieval)")
    verified_at: Optional[str] = Field(default=None, description="ISO timestamp")


class RepositoryComplexity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ContributionComplexity(str, Enum):
    BEGINNER = "BEGINNER"
    BEGINNER_PLUS = "BEGINNER_PLUS"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class SetupComplexity(str, Enum):
    EASY = "EASY"
    MODERATE = "MODERATE"
    HARD = "HARD"


class ContributionType(str, Enum):
    DOCUMENTATION = "DOCUMENTATION"
    TEST = "TEST"
    BUG_FIX = "BUG_FIX"
    SMALL_FEATURE = "SMALL_FEATURE"
    REFACTORING = "REFACTORING"
    TOOLING = "TOOLING"
    OTHER = "OTHER"


class BeginnerSuitability(BaseModel):
    """Multi-dimensional beginner contribution suitability assessment."""
    score: int = Field(default=75, ge=0, le=100, description="Explainable 0 to 100 suitability score")
    tier: ContributionComplexity = Field(default=ContributionComplexity.BEGINNER)
    repository_complexity: RepositoryComplexity = Field(default=RepositoryComplexity.MEDIUM)
    contribution_complexity: ContributionComplexity = Field(default=ContributionComplexity.BEGINNER)
    setup_complexity: SetupComplexity = Field(default=SetupComplexity.EASY)
    contribution_type: ContributionType = Field(default=ContributionType.BUG_FIX)
    positive_signals: List[str] = Field(default_factory=list, description="List of positive beginner indicators")
    warning_signals: List[str] = Field(default_factory=list, description="List of cautionary notices or prerequisites")


class DiagramNode(BaseModel):
    """A single node in a deterministic structured visualization."""
    id: str = Field(description="Unique node identifier")
    label: str = Field(description="Display text")
    node_type: str = Field(default="flow", description="trigger | current | failure | consequence | expected | file | symbol | test")
    provenance: Optional[ProvenanceItem] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DiagramEdge(BaseModel):
    """A directed edge in a deterministic structured visualization."""
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    label: Optional[str] = Field(default=None)
    edge_type: str = Field(default="flow", description="flow | calls | tests | defines | modifies")


class StructuredDiagram(BaseModel):
    """Deterministic structured visualization payload."""
    diagram_type: str = Field(description="FAILURE_FLOW | EXPECTED_VS_CURRENT | CODE_RELATIONSHIP | CONTRIBUTION_FLOW")
    title: str = Field(description="Diagram title")
    description: Optional[str] = Field(default="", description="Contextual explanation")
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)


class DiscussionSummary(BaseModel):
    """Structured GitHub comment and timeline intelligence."""
    total_comments: int = Field(default=0)
    maintainer_comments_count: int = Field(default=0)
    maintainer_guidance: Optional[str] = Field(default=None, description="Direct constraint or advice from maintainers")
    active_contributors: List[str] = Field(default_factory=list, description="Users participating in discussion")
    has_conflicting_work: bool = Field(default=False, description="True if another user claimed work or submitted an open PR")
    conflicting_work_details: Optional[str] = Field(default=None)
    linked_prs: List[Dict[str, Any]] = Field(default_factory=list)
    discussion_summary: str = Field(default="No conflicting work detected in checked GitHub activity.")


class FreshnessMetadata(BaseModel):
    """Decoupled multi-timestamp verification metadata."""
    issue_status_verified_at: str = Field(description="Timestamp of issue state check")
    discussion_verified_at: str = Field(description="Timestamp of comment/timeline check")
    repository_code_verified_at: str = Field(description="Timestamp of codebase indexing check")
    repository_guide_verified_at: str = Field(description="Timestamp of CONTRIBUTING.md check")
    journey_generated_at: str = Field(description="Timestamp of journey assembly")


class GroundedCodeLocation(BaseModel):
    """Verifiable code location cited by LLM."""
    file_path: str = Field(description="Exact relative file path cited from retrieved chunks")
    symbol_name: Optional[str] = Field(default="", description="Qualified symbol name or function name")
    lines: str = Field(default="", description="Line range string (e.g., '45-80')")
    role: str = Field(default="Relevant Code", description="Role of this code in the issue")
    is_verified: bool = Field(default=False, description="Programmatically set to True if file_path exists in context")
    provenance: Optional[ProvenanceItem] = Field(default=None)


class GuidedSolutionStep(BaseModel):
    """Step-by-step beginner-friendly solution instruction."""
    step_number: int = Field(default=1, description="Sequential step index starting at 1")
    title: str = Field(default="Guided Action Step", description="Short action-oriented title")
    description: str = Field(description="Detailed explanation of what to modify or verify")
    target_file: Optional[str] = Field(default=None, description="Target file path if applicable")
    provenance: Optional[ProvenanceItem] = Field(default=None)


class ConceptDetail(BaseModel):
    """Structured beginner education concept card."""
    concept_name: str = Field(description="Name of the required concept")
    short_explanation: str = Field(description="Short, plain-English explanation of what this concept is")
    why_it_matters: str = Field(description="One or two sentences explaining why a developer needs it")
    connection_to_issue: str = Field(description="Explains how this concept directly relates to the issue fix")
    safe_to_ignore: Optional[str] = Field(default=None, description="What a beginner can safely ignore for now")


class RepositoryContributionGuide(BaseModel):
    """Structured repository contribution instructions extracted from CONTRIBUTING.md or CI configs."""
    repo_full_name: str = Field(description="e.g. pallets/flask")
    guide_found: bool = Field(default=False, description="True if CONTRIBUTING.md or CI configs were successfully extracted")
    guide_source: str = Field(default="NOT_FOUND", description="Primary source: CONTRIBUTING.md | .github/workflows/*.yml | NOT_FOUND")
    setup_instructions: Optional[str] = Field(default=None, description="Setup commands or environment setup guidelines")
    test_command: str = Field(default="Not verified — check repository documentation.", description="Verified test command or fallback notice")
    test_command_source: str = Field(default="NOT_VERIFIED", description="Source of test command: CONTRIBUTING.md | .github/workflows/*.yml | NOT_VERIFIED")
    lint_command: Optional[str] = Field(default=None, description="Verified lint command if available")
    lint_command_source: Optional[str] = Field(default="NOT_VERIFIED", description="Source of lint command")
    format_command: Optional[str] = Field(default=None, description="Verified formatting command if available")
    format_command_source: Optional[str] = Field(default="NOT_VERIFIED", description="Source of format command")
    branch_guidance: Optional[str] = Field(default=None, description="Branch naming rules or fork workflow guidelines")
    pull_request_guidance: Optional[str] = Field(default=None, description="PR description guidelines or newsfragment requirements")
    commit_guidance: Optional[str] = Field(default=None, description="Commit message conventions")
    runtime_requirements: Optional[str] = Field(default=None, description="Python or runtime version requirements")
    cla_required: bool = Field(default=False, description="True if CLA / DCO sign-off is required")
    last_verified_at: Optional[str] = Field(default=None, description="ISO timestamp of last verification")
    confidence: str = Field(default="MEDIUM", description="HIGH | MEDIUM | LOW | UNVERIFIED")


class ContributionJourneyStage(BaseModel):
    """A single stage in GitNova's 10-stage Contribution Journey."""
    stage_id: str = Field(description="understand | check_status | learn | explore | investigate | plan | implement | test | prepare_pr | review")
    stage_number: int = Field(description="1 through 10")
    title: str = Field(description="Human-readable title of this stage")
    purpose: str = Field(description="Primary objective of this stage for the contributor")
    explanation: str = Field(description="Grounded, issue-specific narrative explanation")
    steps: List[str] = Field(default_factory=list, description="Actionable steps for the contributor")
    targets: List[str] = Field(default_factory=list, description="Target files, symbols, or modules cited")
    commands: List[str] = Field(default_factory=list, description="Shell or testing commands where applicable")
    concepts: List[ConceptDetail] = Field(default_factory=list, description="Structured concept cards relevant to this stage")
    evidence: List[str] = Field(default_factory=list, description="GitHub signals or codebase evidence supporting this stage")
    warnings: List[str] = Field(default_factory=list, description="Explicit warnings or uncertainty notices")
    completion_criteria: Optional[str] = Field(default="Stage objectives completed.", description="Clear condition defining when this stage is completed")
    diagrams: List[StructuredDiagram] = Field(default_factory=list, description="Deterministic visual diagrams for this stage")
    provenance: Optional[ProvenanceItem] = Field(default=None)


class ContributionJourney(BaseModel):
    """Complete 10-stage GitNova Contribution Journey."""
    journey_version: str = Field(default="4.5", description="Journey schema version")
    repo_full_name: str = Field(description="e.g. pallets/flask")
    github_issue_number: int = Field(description="Numeric issue ID")
    title: str = Field(description="GitHub issue title")
    reporter_username: str = Field(default="community_contributor", description="GitHub issue author")
    availability_status: str = Field(default="LIKELY_AVAILABLE", description="LIKELY_AVAILABLE | CHECK_DISCUSSION | NOT_RECOMMENDED")
    opportunity_confidence: str = Field(default="HIGH", description="HIGH | MEDIUM | LOW")
    beginner_suitability: Optional[BeginnerSuitability] = Field(default=None)
    discussion_summary: Optional[DiscussionSummary] = Field(default=None)
    freshness: Optional[FreshnessMetadata] = Field(default=None)
    last_verified_at: Optional[str] = Field(default=None, description="ISO timestamp of last verification")
    llm_provider: Optional[str] = Field(default="google", description="Active LLM provider used")
    llm_model: Optional[str] = Field(default="gemini-3.6-flash", description="Active model identifier")
    stages: List[ContributionJourneyStage] = Field(default_factory=list, description="Ordered 10-stage journey")


class LLMInvestigationPayload(BaseModel):
    """Structured payload for Phase 1: Code Investigation, Semantic Suitability & Publication Decision."""
    summary: str = Field(description="Plain English explanation of what this issue means for a beginner developer")
    current_behavior: str = Field(description="What currently happens at runtime based strictly on the code evidence")
    expected_behavior: str = Field(description="What behavior is expected when the issue is properly handled")
    why_it_happens: str = Field(description="Deep technical root cause analysis detailing the exact control flow path and failure mechanism")
    relevant_locations: List[GroundedCodeLocation] = Field(default_factory=list, description="Citations to verified code locations in evidence")
    relevant_test_files: List[str] = Field(default_factory=list, description="Relevant existing test files identified from evidence or repository structure")
    structured_concepts: List[ConceptDetail] = Field(default_factory=list, description="2 rich beginner educational concept cards tailored to this specific issue")
    common_pitfalls: List[str] = Field(default_factory=list, description="Common mistakes or things a contributor should avoid touching")
    difficulty_tier: Literal["BEGINNER", "BEGINNER_PLUS", "INTERMEDIATE", "ADVANCED"] = Field(
        default="BEGINNER",
        description=(
            "LLM-assessed contribution difficulty tier. "
            "Must be exactly one of: BEGINNER | BEGINNER_PLUS | INTERMEDIATE | ADVANCED. "
            "BEGINNER: fix touches 1-2 files, isolated logic, no domain expertise needed, well-scoped (docs, typos, simple bug). "
            "BEGINNER_PLUS: well-scoped bug requiring straightforward unit test update. "
            "INTERMEDIATE: requires understanding of module internals, multi-file changes, or framework knowledge. "
            "ADVANCED: requires deep system knowledge, security implications, architectural decisions, cryptography, or broad refactoring."
        )
    )
    difficulty_reasoning: str = Field(
        default="",
        description="Evidence-grounded explanation of why this issue was classified at this difficulty tier, citing specific evidence."
    )
    availability: Literal["AVAILABLE", "NOT_AVAILABLE", "UNCERTAIN"] = Field(
        default="AVAILABLE",
        description=(
            "Contribution availability to an external contributor based on issue discussion, maintainer comments, and PRs. "
            "AVAILABLE: Issue is open, unassigned, and welcoming external PRs. "
            "NOT_AVAILABLE: Discussion shows maintainers are handling it internally, issue is reserved, work is already done in a linked PR, or maintainers explicitly requested no external PRs. "
            "UNCERTAIN: Unclear maintainer consensus, ongoing design debate, or ambiguous claim status."
        )
    )
    availability_reasoning: str = Field(
        default="",
        description="Evidence-grounded explanation of availability, citing specific maintainer comments, PRs, or labels."
    )
    beginner_suitability: Literal["SUITABLE", "NOT_SUITABLE", "UNCERTAIN"] = Field(
        default="SUITABLE",
        description=(
            "Beginner suitability assessment. "
            "SUITABLE: Well-isolated, safe, approachable for a first-time contributor, zero architectural risk. "
            "NOT_SUITABLE: Security/CVE vulnerabilities, auth/crypto architecture, broad refactoring across many call sites, major dialect/schema migrations, or high-risk infrastructure. "
            "UNCERTAIN: Ambiguous technical requirements or complex setup prerequisites."
        )
    )
    evidence_sufficiency: Literal["SUFFICIENT", "INSUFFICIENT"] = Field(
        default="SUFFICIENT",
        description="SUFFICIENT if retrieved codebase and issue evidence are concrete and verifiable; INSUFFICIENT if key context is missing."
    )
    publication_decision: Literal["PUBLISH", "REJECT", "REVIEW_REQUIRED"] = Field(
        default="PUBLISH",
        description=(
            "Final publication recommendation for GitNova beginner feed. "
            "PUBLISH: AVAILABLE + SUITABLE + BEGINNER/BEGINNER_PLUS + SUFFICIENT evidence. "
            "REJECT: NOT_AVAILABLE, NOT_SUITABLE, ADVANCED/INTERMEDIATE, security/CVE, broad refactor, or maintainer restriction. "
            "REVIEW_REQUIRED: UNCERTAIN availability/suitability or edge cases requiring human review."
        )
    )
    publication_reason: str = Field(
        default="",
        description="Concise evidence-grounded explanation of the publication decision."
    )


class LLMPlanPayload(BaseModel):
    """Structured payload for Phase 2: Grounded Planning & Minimal Change."""
    minimal_change_area: str = Field(description="Smallest plausible code modification area supported by evidence")
    step_by_step_plan: List[GuidedSolutionStep] = Field(default_factory=list, description="3 to 5 concrete, ordered guided solution steps referencing exact verified symbols")
    regression_test_strategy: str = Field(description="Concrete guidance on how to write a regression test verifying the fix")
    suggested_test_command: str = Field(description="Exact repository test command to run for verification")


class LLMIssueExplanationPayload(BaseModel):
    """Lean payload structure for backward compatibility."""
    summary: str = Field(description="Plain English explanation of what this issue means for a beginner developer")
    why_it_happens: str = Field(description="Technical root cause analysis based strictly on retrieved codebase evidence")
    prerequisite_concepts: List[str] = Field(default_factory=list, description="Key concepts a beginner must understand first before fixing")
    structured_concepts: List[ConceptDetail] = Field(default_factory=list, description="Rich beginner educational concept cards")
    step_by_step_plan: List[GuidedSolutionStep] = Field(default_factory=list, description="Ordered, beginner-friendly guided solution steps")
    relevant_locations: List[GroundedCodeLocation] = Field(default_factory=list, description="Programmatically verified code locations")
    common_pitfalls: List[str] = Field(default_factory=list, description="Common mistakes or considerations when implementing the fix")


class IssueExplanation(BaseModel):
    """Complete grounded issue explanation structure for website rendering."""
    status: str = Field(default="SUCCESS", description="SUCCESS | INSUFFICIENT_EVIDENCE")
    summary: str = Field(description="Plain English explanation of what this issue means for a beginner developer")
    why_it_happens: str = Field(description="Technical root cause analysis based strictly on retrieved codebase evidence")
    prerequisite_concepts: List[str] = Field(default_factory=list, description="Key concepts a beginner must understand first before fixing")
    structured_concepts: List[ConceptDetail] = Field(default_factory=list, description="Rich beginner educational concept cards")
    step_by_step_plan: List[GuidedSolutionStep] = Field(default_factory=list, description="Ordered, beginner-friendly guided solution steps")
    relevant_locations: List[GroundedCodeLocation] = Field(default_factory=list, description="Programmatically verified code locations")
    common_pitfalls: List[str] = Field(default_factory=list, description="Common mistakes or considerations when implementing the fix")
    difficulty_tier: Optional[Literal["BEGINNER", "BEGINNER_PLUS", "INTERMEDIATE", "ADVANCED"]] = Field(default="BEGINNER")
    difficulty_reasoning: Optional[str] = Field(default="")
    availability: Optional[Literal["AVAILABLE", "NOT_AVAILABLE", "UNCERTAIN"]] = Field(default="AVAILABLE")
    availability_reasoning: Optional[str] = Field(default="")
    beginner_suitability_decision: Optional[Literal["SUITABLE", "NOT_SUITABLE", "UNCERTAIN"]] = Field(default="SUITABLE")
    evidence_sufficiency: Optional[Literal["SUFFICIENT", "INSUFFICIENT"]] = Field(default="SUFFICIENT")
    publication_decision: Optional[Literal["PUBLISH", "REJECT", "REVIEW_REQUIRED"]] = Field(default="PUBLISH")
    publication_reason: Optional[str] = Field(default="")
    disclaimer: Optional[str] = Field(default=None, description="Set if evidence is partial or unverified citations were pruned")
    beginner_suitability: Optional[BeginnerSuitability] = Field(default=None)
    discussion_summary: Optional[DiscussionSummary] = Field(default=None)
    structured_diagrams: List[StructuredDiagram] = Field(default_factory=list)
    freshness: Optional[FreshnessMetadata] = Field(default=None)
    contribution_journey: Optional[ContributionJourney] = Field(default=None, description="Structured 10-stage Contribution Journey")
    llm_provider: Optional[str] = Field(default="google", description="LLM provider used")
    llm_model: Optional[str] = Field(default="gemini-3.6-flash", description="Model used")

    @field_validator('step_by_step_plan', mode='before')
    @classmethod
    def normalize_step_by_step_plan(cls, v: Any) -> Any:
        if isinstance(v, list):
            normalized = []
            for idx, item in enumerate(v, 1):
                if isinstance(item, str):
                    normalized.append({
                        "step_number": idx,
                        "title": f"Step {idx}",
                        "description": item,
                        "target_file": None
                    })
                else:
                    normalized.append(item)
            return normalized
        return v
