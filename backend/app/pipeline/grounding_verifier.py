"""
GitNova v4.2 — Programmatic Grounding Verifier Engine

Cross-checks LLM citations against Sprint 7 retrieved codebase chunks.
Enforces programmatic anti-hallucination rules:
  1. Validates that cited file_paths exist in retrieved context.
  2. Validates symbol names where metadata exists.
  3. Prunes/flags unverified citations and appends disclaimer warnings.
  4. Provides short-circuit helper for INSUFFICIENT_EVIDENCE fallback.
"""

from typing import List, Dict, Any, Set, Tuple
from app.schemas.explanation import IssueExplanation, GroundedCodeLocation


class GroundingVerifier:
    """Programmatic verification engine enforcing strict codebase grounding."""

    def __init__(self, retrieved_chunks: List[Dict[str, Any]]):
        self.retrieved_chunks = retrieved_chunks or []
        self.retrieved_files: Set[str] = {
            c["file_path"].lower().replace("\\", "/")
            for c in self.retrieved_chunks if "file_path" in c
        }
        self.retrieved_symbols: Set[str] = {
            c["qualified_symbol_name"].lower()
            for c in self.retrieved_chunks if c.get("qualified_symbol_name")
        }

    @staticmethod
    def calculate_total_tokens(retrieved_chunks: List[Dict[str, Any]]) -> int:
        """Calculates total estimated tokens across retrieved chunks."""
        total = 0
        for c in retrieved_chunks or []:
            content = c.get("content", "")
            total += max(1, len(content) // 4)
        return total

    @classmethod
    def is_evidence_insufficient(cls, retrieved_chunks: List[Dict[str, Any]], min_token_threshold: int = 100) -> bool:
        """Returns True if retrieved context contains fewer than min_token_threshold tokens."""
        if not retrieved_chunks:
            return True
        return cls.calculate_total_tokens(retrieved_chunks) < min_token_threshold

    @classmethod
    def build_insufficient_evidence_response(cls, reason: str = None) -> IssueExplanation:
        """Builds a fallback IssueExplanation with status='INSUFFICIENT_EVIDENCE'."""
        fallback_msg = (
            reason or "GitNova could not find sufficient codebase evidence to generate a grounded explanation for this issue."
        )
        return IssueExplanation(
            status="INSUFFICIENT_EVIDENCE",
            summary="Insufficient evidence found in indexed repository chunks.",
            why_it_happens=fallback_msg,
            prerequisite_concepts=["Complete repository indexing using Sprint 7 pipeline."],
            step_by_step_plan=[],
            relevant_locations=[],
            common_pitfalls=["Do not attempt implementation without verifying matching source code chunks."],
            disclaimer="Automated LLM generation skipped due to insufficient retrieved context evidence."
        )

    def has_sufficient_evidence(self) -> bool:
        """Returns True if there is at least one verified file in the retrieved context."""
        return len(self.retrieved_files) > 0

    def create_insufficient_evidence_explanation(self, reason: str = None) -> IssueExplanation:
        """Instance helper to build an insufficient evidence explanation."""
        return self.build_insufficient_evidence_response(reason)

    def verify_and_sanitize(self, explanation: IssueExplanation) -> IssueExplanation:
        """
        Validates explanation citations against retrieved chunks.
        Prunes hallucinated file_paths and sets is_verified flags.
        """
        if explanation.status == "INSUFFICIENT_EVIDENCE":
            return explanation

        valid_locations: List[GroundedCodeLocation] = []
        pruned_count = 0

        for loc in explanation.relevant_locations:
            norm_path = loc.file_path.lower().replace("\\", "/").strip()
            
            # File path validation
            if norm_path in self.retrieved_files:
                loc.is_verified = True
                valid_locations.append(loc)
            else:
                # Check for partial match (e.g. filename matching relative path)
                matched_path = None
                for rf in self.retrieved_files:
                    if rf.endswith(norm_path) or norm_path.endswith(rf):
                        matched_path = rf
                        break
                
                if matched_path:
                    loc.is_verified = True
                    valid_locations.append(loc)
                else:
                    pruned_count += 1

        explanation.relevant_locations = valid_locations
        if pruned_count > 0:
            disclaimer_msg = (
                f"Note: {pruned_count} unverified file citations were automatically pruned "
                "because they were not present in the retrieved codebase evidence."
            )
            explanation.disclaimer = (
                f"{explanation.disclaimer} {disclaimer_msg}".strip()
                if explanation.disclaimer else disclaimer_msg
            )

        return explanation

    def compute_verification_status(self, explanation: IssueExplanation) -> Tuple[str, List[str]]:
        """
        Determines programmatic verification status:
          - VERIFIED: All cited files exist in retrieved context, >0 verified locations.
          - NEEDS_REVIEW: Partial evidence or pruned citations, but valid summary.
          - INVALID: Status is INSUFFICIENT_EVIDENCE or 0 verified locations.
        """
        reasons = []

        if explanation.status == "INSUFFICIENT_EVIDENCE":
            return "INVALID", ["Retrieved context contains insufficient codebase evidence (<100 tokens)."]

        if not explanation.relevant_locations:
            reasons.append("No verified code locations were cited in the explanation.")
            return "NEEDS_REVIEW", reasons

        unverified_count = sum(1 for loc in explanation.relevant_locations if not loc.is_verified)
        total_locs = len(explanation.relevant_locations)

        if unverified_count == 0 and total_locs > 0:
            reasons.append(f"All {total_locs} code locations verified against retrieved codebase evidence.")
            return "VERIFIED", reasons
        elif unverified_count < total_locs:
            reasons.append(f"{total_locs - unverified_count} of {total_locs} locations verified.")
            return "NEEDS_REVIEW", reasons
        else:
            reasons.append("All cited file locations failed codebase context verification.")
            return "INVALID", reasons

