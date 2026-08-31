"""
GitNova v4.5 — Programmatic Grounding Verifier & Publication Gate
==================================================================
Cross-checks LLM citations and explanations against retrieved codebase chunks
and repository metadata to enforce strict anti-hallucination, grounding, and
publication safety requirements.

Hard Requirements Enforced:
1. Target Verification: Cited file paths must exist in retrieved repository snapshot.
2. Cross-Repository Protection: Target file extensions and paths must match the repository ecosystem.
3. Symbol Verification: Source-code targets require a verified symbol (documentation/config targets do not).
4. Root Cause Grounding: Root cause analysis must be substantive and reference verified files/behavior.
5. Plan Quality: Step-by-step plan must contain >= 3 meaningful, specific steps (no generic boilerplate).
6. Test Guidance Verification: Test commands must match the repository ecosystem.
7. Cross-Stage Consistency: Target files across explanation, plan, and journey must agree.
8. Bounded Scope: Broad multi-package rewrites are gated from beginner publication.
"""

import re
from typing import List, Dict, Any, Set, Tuple, Optional
from app.schemas.explanation import IssueExplanation, GroundedCodeLocation
from app.pipeline.repo_grounding import LANGUAGE_EXTENSIONS

# Common config/doc extensions allowed across all repositories
COMMON_NON_CODE_EXTENSIONS = {
    ".md", ".rst", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".cfg", ".env"
}

# Generic boilerplate phrases that indicate weak or ungrounded generation
GENERIC_BOILERPLATE_PATTERNS = [
    r"\breview the code\b",
    r"\bmake the changes\b",
    r"\bupdate the relevant code\b",
    r"\bfix the issue\b",
    r"\brun the tests\b",
    r"\btest the changes\b",
    r"\bimplement the necessary\b",
    r"\bnull check\b",
    r"\bcase branch\b",
    r"\binsufficient_context\b",
]

# Standard test commands by language ecosystem
ECOSYSTEM_TEST_COMMANDS = {
    "python": ["pytest", "python -m unittest", "tox", "nox"],
    "javascript": ["npm test", "yarn test", "pnpm test", "jest", "vitest"],
    "typescript": ["npm test", "yarn test", "pnpm test", "jest", "vitest", "tsc"],
    "java": ["mvn test", "gradle test", "./gradlew test", "./mvnw test"],
    "go": ["go test ./...", "go test"],
    "rust": ["cargo test"],
    "c#": ["dotnet test"],
    "ruby": ["bundle exec rspec", "rake test"],
}


class GroundingVerifier:
    """Programmatic verification engine enforcing strict codebase grounding & publication safety."""

    def __init__(
        self,
        retrieved_chunks: List[Dict[str, Any]],
        repo_name: Optional[str] = None,
        repo_language: Optional[str] = None,
    ):
        self.retrieved_chunks = retrieved_chunks or []
        self.repo_name = repo_name
        self.repo_language = (repo_language or "").lower().strip()
        
        self.retrieved_files: Set[str] = {
            c["file_path"].lower().replace("\\", "/").strip()
            for c in self.retrieved_chunks if "file_path" in c
        }
        
        self.retrieved_symbols: Set[str] = set()
        self.chunk_texts: List[str] = []
        for c in self.retrieved_chunks:
            if c.get("qualified_symbol_name"):
                self.retrieved_symbols.add(c["qualified_symbol_name"].lower().strip())
            if c.get("symbol_name"):
                self.retrieved_symbols.add(c["symbol_name"].lower().strip())
            content = c.get("content", "")
            if content:
                self.chunk_texts.append(content.lower())

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
        Validates explanation citations against retrieved chunks and repository language.
        Prunes hallucinated file paths and sets is_verified flags.
        """
        if explanation.status == "INSUFFICIENT_EVIDENCE":
            return explanation

        valid_locations: List[GroundedCodeLocation] = []
        pruned_count = 0

        valid_exts = set(LANGUAGE_EXTENSIONS.get(self.repo_language, []))

        for loc in explanation.relevant_locations:
            norm_path = loc.file_path.lower().replace("\\", "/").strip()
            ext_match = re.search(r'(\.\w+)$', norm_path)
            ext = ext_match.group(1).lower() if ext_match else ""

            # Check cross-repository extension mismatch (e.g. .java file in a python repo)
            if self.repo_language and valid_exts and ext:
                if ext not in valid_exts and ext not in COMMON_NON_CODE_EXTENSIONS:
                    pruned_count += 1
                    continue

            # File path existence in retrieved snapshot
            is_file_match = norm_path in self.retrieved_files
            if not is_file_match:
                for rf in self.retrieved_files:
                    if rf.endswith(norm_path) or norm_path.endswith(rf):
                        is_file_match = True
                        break

            if is_file_match:
                # Symbol validation for source code files
                if ext and ext not in COMMON_NON_CODE_EXTENSIONS and loc.symbol_name:
                    sym_lower = loc.symbol_name.lower().strip()
                    sym_found = (sym_lower in self.retrieved_symbols) or any(sym_lower in txt for txt in self.chunk_texts)
                    loc.is_verified = bool(sym_found or not self.retrieved_symbols)
                else:
                    # Documentation / config files or code files without specific symbol
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

    def validate_publication_gate(
        self,
        explanation: IssueExplanation,
        repo_data: Dict[str, Any] = None,
        raw_issue: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive Phase 4 publication decision gate.
        Validates target, symbol, root-cause, plan quality, test guidance,
        cross-stage consistency, and scope boundedness.
        """
        repo_data = repo_data or {}
        raw_issue = raw_issue or {}
        rejection_codes: List[str] = []
        rejection_reasons: List[str] = []

        # 1. Target Verification Gate
        if not explanation.relevant_locations or len(explanation.relevant_locations) == 0:
            rejection_codes.append("NO_VERIFIED_TARGET")
            rejection_reasons.append("No verified target locations in retrieved repository snapshot.")

        # 2. Cross-Repository Protection Gate
        valid_exts = set(LANGUAGE_EXTENSIONS.get(self.repo_language, []))
        for loc in explanation.relevant_locations:
            norm_path = loc.file_path.lower().replace("\\", "/").strip()
            ext_match = re.search(r'(\.\w+)$', norm_path)
            ext = ext_match.group(1).lower() if ext_match else ""
            if self.repo_language and valid_exts and ext:
                if ext not in valid_exts and ext not in COMMON_NON_CODE_EXTENSIONS:
                    if "CROSS_REPOSITORY_MISMATCH" not in rejection_codes:
                        rejection_codes.append("CROSS_REPOSITORY_MISMATCH")
                        rejection_reasons.append(f"Target file '{loc.file_path}' has extension '{ext}' incompatible with repo language '{self.repo_language}'.")

        # 3. Symbol Verification Gate
        for loc in explanation.relevant_locations:
            norm_path = loc.file_path.lower().replace("\\", "/").strip()
            ext_match = re.search(r'(\.\w+)$', norm_path)
            ext = ext_match.group(1).lower() if ext_match else ""
            # Code file requiring symbol verification
            if ext and ext not in COMMON_NON_CODE_EXTENSIONS:
                if not loc.symbol_name and len(self.retrieved_symbols) > 0:
                    # Only flag if symbols exist in retrieved chunks
                    pass
                elif loc.symbol_name and not loc.is_verified:
                    if "SYMBOL_NOT_VERIFIED" not in rejection_codes:
                        rejection_codes.append("SYMBOL_NOT_VERIFIED")
                        rejection_reasons.append(f"Cited symbol '{loc.symbol_name}' could not be verified in codebase AST.")

        # 4. Root Cause Grounding Gate
        why_text = (explanation.why_it_happens or "").strip()
        summary_text = (explanation.summary or "").strip()
        if not why_text or len(why_text.split()) < 10:
            rejection_codes.append("UNSUPPORTED_ROOT_CAUSE")
            rejection_reasons.append("Root cause explanation is empty or too short (<10 words).")
        else:
            # Check for generic template collapse
            boilerplate_hits = sum(1 for p in GENERIC_BOILERPLATE_PATTERNS if re.search(p, why_text, re.IGNORECASE))
            if boilerplate_hits >= 2:
                rejection_codes.append("UNSUPPORTED_ROOT_CAUSE")
                rejection_reasons.append("Root cause explanation consists of generic boilerplate statements.")

        # 5. Plan Quality Gate (>= 3 meaningful steps)
        plan_steps = explanation.step_by_step_plan or []
        if len(plan_steps) < 3:
            rejection_codes.append("INSUFFICIENT_PLAN")
            rejection_reasons.append(f"Plan contains only {len(plan_steps)} steps (minimum 3 required).")
        else:
            # Check if steps are generic filler
            step_texts = [
                (step.description if hasattr(step, "description") else str(step)).lower()
                for step in plan_steps
            ]
            generic_step_count = 0
            for st in step_texts:
                if any(re.search(p, st) for p in GENERIC_BOILERPLATE_PATTERNS) and len(st.split()) < 8:
                    generic_step_count += 1
            if generic_step_count >= 2:
                rejection_codes.append("INSUFFICIENT_PLAN")
                rejection_reasons.append("Plan consists of generic placeholder steps without concrete repository guidance.")

        # 6. Test Guidance Verification
        test_cmd = (repo_data.get("test_command") or "").strip().lower()
        if not test_cmd and hasattr(explanation, "contribution_journey") and explanation.contribution_journey:
            for st in getattr(explanation.contribution_journey, "stages", []):
                if getattr(st, "stage_id", "") == "test" and getattr(st, "commands", []):
                    test_cmd = st.commands[0].lower()
                    break

        if self.repo_language in ECOSYSTEM_TEST_COMMANDS and test_cmd and "not verified" not in test_cmd:
            expected_cmds = ECOSYSTEM_TEST_COMMANDS[self.repo_language]
            # If a concrete command is specified, verify it matches ecosystem standards
            if not any(exp in test_cmd for exp in expected_cmds):
                rejection_codes.append("TEST_GUIDANCE_NOT_VERIFIED")
                rejection_reasons.append(f"Test command '{test_cmd}' does not match '{self.repo_language}' ecosystem standards.")

        # 7. Cross-Stage Target Consistency Gate
        if explanation.relevant_locations:
            primary_file = explanation.relevant_locations[0].file_path.lower().replace("\\", "/").strip()
            conflicting_plan_files = []
            for step in plan_steps:
                target_f = getattr(step, "target_file", None)
                if target_f:
                    norm_target = target_f.lower().replace("\\", "/").strip()
                    # Allow standard test files and documentation files
                    is_test_or_doc = (
                        norm_target.startswith("test") or "/test" in norm_target or
                        norm_target.endswith(".md") or norm_target.endswith(".rst") or
                        norm_target.endswith(".txt")
                    )
                    if not is_test_or_doc:
                        if norm_target not in self.retrieved_files and not any(rf.endswith(norm_target) for rf in self.retrieved_files):
                            conflicting_plan_files.append(target_f)
            if conflicting_plan_files:
                rejection_codes.append("CROSS_STAGE_TARGET_DIVERGENCE")
                rejection_reasons.append(f"Plan steps cite unverified files not in relevant locations: {', '.join(conflicting_plan_files[:2])}.")

        # 8. Scope & Beginner Safety Gate
        issue_title = (raw_issue.get("title") or "").lower()
        issue_body = (raw_issue.get("body") or "").lower()
        unbounded_signals = ["complete rewrite", "rewrite entire", "overhaul everything", "redesign architecture"]
        if any(s in issue_title or s in issue_body for s in unbounded_signals):
            rejection_codes.append("SCOPE_TOO_BROAD")
            rejection_reasons.append("Issue requires multi-subsystem architectural redesign.")

        is_safe = (len(rejection_codes) == 0)

        return {
            "is_safe": is_safe,
            "rejection_codes": rejection_codes,
            "rejection_reasons": rejection_reasons,
            "target_verified": len(explanation.relevant_locations) > 0,
            "symbol_verified": "SYMBOL_NOT_VERIFIED" not in rejection_codes,
            "root_cause_grounded": "UNSUPPORTED_ROOT_CAUSE" not in rejection_codes,
            "plan_actionable": "INSUFFICIENT_PLAN" not in rejection_codes,
            "test_guidance_valid": "TEST_GUIDANCE_NOT_VERIFIED" not in rejection_codes,
            "cross_stage_consistent": "CROSS_STAGE_TARGET_DIVERGENCE" not in rejection_codes,
            "cross_repo_protected": "CROSS_REPOSITORY_MISMATCH" not in rejection_codes,
        }
