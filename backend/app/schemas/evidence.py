"""
GitNova v4.5 — EvidencePackage Schema Definition

Strict Pydantic schemas representing all raw and extracted evidence available
for a specific GitHub issue before any LLM reasoning takes place.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from app.schemas.explanation import ProvenanceType, ProvenanceItem


class CodeEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str
    file_path: str
    symbol_name: Optional[str] = None
    qualified_symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    info_class: str = "SOURCE_CODE"
    start_line: int
    end_line: int
    content: str
    contextual_header: Optional[str] = None
    commit_sha: Optional[str] = None
    retrieval_method: str = "hybrid_rrf"
    retrieval_score: float = 0.0


class TestEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: str
    file_path: str
    test_function_name: Optional[str] = None
    start_line: int
    end_line: int
    content: str
    contextual_header: Optional[str] = None


class IssueEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_full_name: str
    github_issue_number: int
    title: str
    body: str
    state: str = "open"
    reporter_username: str
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    comments_count: int = 0
    html_url: str


class StatusEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    availability_status: str = "CHECK_DISCUSSION"
    confidence: str = "HIGH"
    is_assigned: bool = False
    has_positive_labels: bool = False
    has_warning_labels: bool = False
    linked_prs_count: int = 0
    linked_prs: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_statements: List[str] = Field(default_factory=list)
    warning_statements: List[str] = Field(default_factory=list)
    last_verified_at: str


class RepositoryEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repo_full_name: str
    primary_language: str
    default_branch: str = "main"
    current_commit_sha: str
    package_manager: str = "NOT_VERIFIED"
    test_framework: str = "NOT_VERIFIED"
    test_command: str = "NOT_VERIFIED"
    test_command_source: str = "NOT_VERIFIED"
    lint_command: Optional[str] = None
    lint_command_source: str = "NOT_VERIFIED"
    format_command: Optional[str] = None
    format_command_source: str = "NOT_VERIFIED"
    setup_instructions: Optional[str] = None
    contributing_guidelines_summary: Optional[str] = None
    cla_required: bool = False


class DiscussionEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")

    has_discussion_data: bool = False
    timeline_events_count: int = 0
    maintainer_comments: List[Dict[str, Any]] = Field(default_factory=list)
    contributor_comments: List[Dict[str, Any]] = Field(default_factory=list)
    discussion_summary: Optional[str] = None
    maintainer_intent: Optional[str] = None
    conflicting_work_detected: bool = False


class EvidencePackage(BaseModel):
    """Complete, strictly-typed evidence package supplied to LLM reasoning phases."""
    model_config = ConfigDict(extra="ignore")

    issue: IssueEvidence
    status: StatusEvidence
    repository: RepositoryEvidence
    code_evidence: List[CodeEvidenceItem] = Field(default_factory=list)
    test_evidence: List[TestEvidenceItem] = Field(default_factory=list)
    discussion: DiscussionEvidence
    package_timestamp: str
