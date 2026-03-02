"""
GitNova Quality Scoring System
===============================
Computes a composite quality score (0–100) from 4 sub-metrics:
- Specificity (30%): count of concrete identifiers
- Repo Alignment (25%): file extensions & directory matching
- Actionability (25%): numbered steps, file paths, function names
- Hallucination Risk (20%): inverted score for placeholder/generic patterns
"""

import re
from app.pipeline.repo_grounding import LANGUAGE_EXTENSIONS

# Common placeholder paths that suggest hallucination
PLACEHOLDER_PATHS = [
    "src/components/", "src/utils/", "src/types/",
    "src/config/", "src/core/", "src/services/",
    "src/App.", "src/index.",
]

# Generic frameworks that are commonly hallucinated into wrong repos
GENERIC_FRAMEWORKS = {
    ".tsx": ["react", "next", "solid", "vue"],
    ".jsx": ["react", "next"],
    ".swift": ["ios", "swift", "apple"],
    ".kt": ["android", "kotlin"],
    ".java": ["java", "android", "spring"],
    ".go": ["go", "golang"],
    ".py": ["python", "django", "flask"],
}


def compute_quality_score(hint_text: str, repo_context: dict) -> dict:
    """
    Compute a composite quality score for an LLM-generated hint.
    
    Returns:
        {
            "specificity": 0-100,
            "repo_alignment": 0-100,
            "actionability": 0-100,
            "hallucination_risk": 0-100 (higher = LESS risky),
            "overall": 0-100,
            "grade": "High" | "Medium" | "Low"
        }
    """
    if not hint_text or hint_text.strip() == "":
        return _empty_score()
    
    specificity = _score_specificity(hint_text)
    repo_alignment = _score_repo_alignment(hint_text, repo_context)
    actionability = _score_actionability(hint_text)
    hallucination_safety = _score_hallucination_safety(hint_text, repo_context)
    
    overall = (
        specificity * 0.30 +
        repo_alignment * 0.25 +
        actionability * 0.25 +
        hallucination_safety * 0.20
    )
    
    overall = round(overall)
    
    if overall >= 70:
        grade = "High"
    elif overall >= 40:
        grade = "Medium"
    else:
        grade = "Low"
    
    return {
        "specificity": round(specificity),
        "repo_alignment": round(repo_alignment),
        "actionability": round(actionability),
        "hallucination_risk": round(hallucination_safety),
        "overall": overall,
        "grade": grade,
    }


def _score_specificity(hint_text: str) -> float:
    """Count concrete identifiers: class names, function calls, file paths."""
    # PascalCase class names
    pascal = len(set(re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', hint_text)))
    # Function calls
    func_calls = len(set(re.findall(r'\b\w+\.\w+\(', hint_text)))
    func_parens = len(set(re.findall(r'\b\w+\(\)', hint_text)))
    # camelCase
    camel = len(set(re.findall(r'\b[a-z]+[A-Z][a-z]+\w*\b', hint_text)))
    # File paths with extensions
    paths = len(set(re.findall(r'`[^`]*\.\w{1,5}`', hint_text)))
    
    total = pascal + func_calls + func_parens + camel + paths
    
    # Scale: 0 identifiers = 0, 3 = 50, 6+ = 90, 10+ = 100
    if total >= 10:
        return 100
    elif total >= 6:
        return 90
    elif total >= 4:
        return 70
    elif total >= 3:
        return 50
    elif total >= 2:
        return 35
    elif total >= 1:
        return 20
    return 0


def _score_repo_alignment(hint_text: str, repo_context: dict) -> float:
    """Check if file extensions match repo language and dirs match top_dirs."""
    valid_exts = repo_context.get("valid_extensions", [])
    top_dirs = repo_context.get("top_dirs", [])
    
    if not valid_exts:
        return 50  # Neutral if we don't know the language
    
    # Find all file extensions in hint
    file_paths = re.findall(r'`([^`]*\.\w{1,5})`', hint_text)
    
    if not file_paths:
        return 30  # No file paths at all = poor alignment
    
    # Check extension matching
    correct_ext_count = 0
    wrong_ext_count = 0
    all_known = set()
    for exts in LANGUAGE_EXTENSIONS.values():
        all_known.update(exts)
    
    config_exts = {".json", ".yml", ".yaml", ".toml", ".xml", ".md", ".txt", ".cfg", ".ini", ".env", ".pro", ".gradle"}
    
    for fp in file_paths:
        ext_match = re.search(r'(\.\w+)$', fp)
        if ext_match:
            ext = ext_match.group(1).lower()
            if ext in config_exts:
                continue  # Config files are always OK
            if ext in valid_exts:
                correct_ext_count += 1
            elif ext in all_known:
                wrong_ext_count += 1
    
    total_checked = correct_ext_count + wrong_ext_count
    if total_checked == 0:
        ext_score = 50
    else:
        ext_score = (correct_ext_count / total_checked) * 100
    
    # Check directory matching
    dir_score = 50  # Neutral default
    if top_dirs:
        hint_lower = hint_text.lower()
        matching_dirs = sum(1 for d in top_dirs if d.rstrip("/").lower() in hint_lower)
        if matching_dirs >= 2:
            dir_score = 100
        elif matching_dirs == 1:
            dir_score = 70
        else:
            dir_score = 30
    
    return ext_score * 0.7 + dir_score * 0.3


def _score_actionability(hint_text: str) -> float:
    """Check for numbered steps, file paths, and function/class references."""
    score = 0
    
    # Has numbered steps?
    steps = re.findall(r'^\s*\d+\.', hint_text, re.MULTILINE)
    if len(steps) >= 3:
        score += 35
    elif len(steps) >= 2:
        score += 25
    elif len(steps) >= 1:
        score += 15
    
    # Has file paths?
    paths = re.findall(r'`[^`]*(?:/|\\)[^`]*`', hint_text)
    if len(paths) >= 2:
        score += 30
    elif len(paths) >= 1:
        score += 20
    
    # Has function/class names?
    identifiers = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', hint_text)
    identifiers += re.findall(r'\b\w+\.\w+\(', hint_text)
    if len(identifiers) >= 2:
        score += 35
    elif len(identifiers) >= 1:
        score += 20
    
    return min(score, 100)


def _score_hallucination_safety(hint_text: str, repo_context: dict) -> float:
    """
    Higher = SAFER (less hallucination risk).
    Checks for placeholder paths and framework mismatches.
    """
    score = 100  # Start perfect, deduct for red flags
    
    hint_lower = hint_text.lower()
    
    # Deduct for placeholder paths
    placeholder_hits = sum(1 for p in PLACEHOLDER_PATHS if p.lower() in hint_lower)
    score -= placeholder_hits * 15
    
    # Deduct for wrong-framework file extensions
    valid_exts = repo_context.get("valid_extensions", [])
    topics = [t.lower() for t in repo_context.get("topics", [])]
    lang = repo_context.get("language_lower", "")
    
    for ext, frameworks in GENERIC_FRAMEWORKS.items():
        if ext not in valid_exts and ext in hint_lower:
            # This extension shouldn't be in this repo
            score -= 20
    
    # Deduct for "INSUFFICIENT CONTEXT" (signals quality issue)
    if "insufficient context" in hint_lower:
        score -= 50
    
    return max(score, 0)


def _empty_score() -> dict:
    return {
        "specificity": 0,
        "repo_alignment": 0,
        "actionability": 0,
        "hallucination_risk": 0,
        "overall": 0,
        "grade": "Low",
    }
