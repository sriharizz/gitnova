"""
GitNova v4.2 — Deterministic Issue Difficulty Engine

Calculates issue difficulty (0-100) and assigns difficulty_tier
(BEGINNER | INTERMEDIATE | ADVANCED) using 100% deterministic code signals.
Requires zero user questionnaires.
"""

from typing import List, Dict, Any, Tuple


def compute_issue_difficulty(
    retrieved_chunks: List[Dict[str, Any]],
    repo_complexity: float = 50.0,
    issue_body: str = ""
) -> Tuple[float, str]:
    """
    Computes deterministic difficulty score (0-100) and assigns tier:
      - BEGINNER     (0 <= score <= 35)
      - INTERMEDIATE (36 <= score <= 70)
      - ADVANCED     (71 <= score <= 100)
    """
    # 1. Retrieval Candidate Footprint (40%)
    unique_files = {
        c.get("file_path", "").lower()
        for c in (retrieved_chunks or [])
        if c.get("file_path")
    }
    file_count = len(unique_files)
    if file_count <= 2:
        file_score = 10.0
    elif file_count <= 4:
        file_score = 50.0
    else:
        file_score = 90.0

    # 2. Repository Onboarding Complexity (30%)
    repo_comp_score = max(0.0, min(100.0, float(repo_complexity or 50.0)))

    # 3. Symbol Depth & Generics (20%)
    symbol_score = 20.0
    for chunk in (retrieved_chunks or []):
        content = chunk.get("content", "")
        # Check for deep structural keywords / generics / trait bounds
        if any(kw in content for kw in ["generic", "template<", "trait ", "interface ", "abstract class", "async fn"]):
            symbol_score = 80.0
            break
        elif "class " in content or "def " in content:
            symbol_score = 40.0

    # 4. Issue Description Specificity (10%)
    body_str = (issue_body or "").strip()
    word_count = len(body_str.split())
    if word_count > 150 or "```" in body_str or "Traceback" in body_str:
        brevity_score = 10.0  # Detailed description with logs = easier to locate
    elif word_count > 50:
        brevity_score = 40.0
    else:
        brevity_score = 80.0  # Short / vague description = harder

    # Composite Score Calculation
    composite = (
        0.40 * file_score +
        0.30 * repo_comp_score +
        0.20 * symbol_score +
        0.10 * brevity_score
    )

    difficulty_score = round(max(0.0, min(100.0, composite)), 1)

    if difficulty_score <= 35.0:
        difficulty_tier = "BEGINNER"
    elif difficulty_score <= 70.0:
        difficulty_tier = "INTERMEDIATE"
    else:
        difficulty_tier = "ADVANCED"

    return difficulty_score, difficulty_tier
