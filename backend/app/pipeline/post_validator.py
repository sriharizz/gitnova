"""
GitNova Post-Generation Validator
==================================
Runs automated checks on LLM output to detect:
1. File extension mismatches with repo language
2. Boilerplate/generic verb usage
3. Low tactical specificity (no concrete identifiers)
"""

import re
from app.pipeline.repo_grounding import LANGUAGE_EXTENSIONS

# Banned boilerplate phrases (case-insensitive)
BANNED_PHRASES = [
    r"\breview the\b",
    r"\binvestigate the\b",
    r"\bfix the\b",
    r"\btest the\b",
    r"\bupdate the\b",
    r"\bmodify the\b",
    r"\bcheck the\b",
    r"\bensure the\b",
    r"\bensure that\b",
    r"\bresearch and understand\b",
    r"\bresearch the\b",
    r"\bverify the\b",
    r"\banalyze the\b",
    r"\bimplement the necessary\b",
    r"\bthoroughly test\b",
    r"\bcomprehensive test\b",
    r"\btest the changes\b",
    r"\btest the modified\b",
    r"\bensure compatibility\b",
    r"\bensure correctness\b",
]

# All known extensions from all languages (flattened)
ALL_KNOWN_EXTENSIONS = set()
for exts in LANGUAGE_EXTENSIONS.values():
    ALL_KNOWN_EXTENSIONS.update(exts)


def validate_llama_output(ai_hint: str, repo_language: str) -> tuple:
    """
    Validate an LLM-generated hint against strict hallucination/template collapse rules.
    
    Args:
        ai_hint: The raw text string from Llama 3
        repo_language: The string name of the repository language
        
    Returns:
        (passed: bool, failures: list[str])
    """
    failures = []
    
    if not ai_hint or ai_hint.strip() == "":
        return False, ["Empty hint text"]
        
    hint_lower = ai_hint.lower()
    
    # 1. Check for template collapse / generic guesses
    banned_guesses = ["null check", "case branch", "insufficient_context"]
    for guess in banned_guesses:
        if guess in hint_lower:
            failures.append(f"Template collapse detected: Contains banned phrase '{guess}'")
            
    # 2. Check for Hallucinated Extensions
    language_lower = repo_language.lower()
    backend_langs = ["python", "java", "c++", "c", "go", "rust", "ruby"]
    
    if language_lower in backend_langs:
        # Check if the hint mentions .ts or .tsx
        if ".ts`" in hint_lower or ".tsx`" in hint_lower or re.search(r'\b\w+\.tsx?\b', hint_lower):
            failures.append(f"Extension Hallucination: Suggested .ts/.tsx files for a {repo_language} repository")
            
    # 3. Keep existing boilerplate and specificity checks
    boilerplate_failures = _check_boilerplate(ai_hint)
    failures.extend(boilerplate_failures)
    
    specificity_failures = _check_specificity(ai_hint)
    failures.extend(specificity_failures)
    
    passed = len(failures) == 0
    return passed, failures


def validate_hint_from_csv(hint_text: str, repo_name: str, repo_context: dict) -> tuple:
    """
    Validate an existing hint from CSV data (retroactive filtering).
    Same checks but more lenient on specificity.
    """
    failures = []
    
    if not hint_text or hint_text.strip() == "":
        return False, ["Empty hint text"]
    
    # Check 1: File extension consistency
    ext_failures = _check_file_extensions(hint_text, repo_context)
    failures.extend(ext_failures)
    
    # Check 2: Boilerplate detection
    boilerplate_failures = _check_boilerplate(hint_text)
    failures.extend(boilerplate_failures)
    
    passed = len(failures) == 0
    return passed, failures


def _check_file_extensions(hint_text: str, repo_context: dict) -> list:
    """Check that file paths in the hint use extensions matching the repo language."""
    failures = []
    
    valid_exts = repo_context.get("valid_extensions", [])
    if not valid_exts:
        return []  # Can't validate if we don't know the language
    
    # Find all file paths mentioned (e.g., `src/foo/bar.py` or src/foo/bar.ts)
    file_paths = re.findall(r'`([^`]*\.\w{1,5})`', hint_text)
    # Also catch non-backticked paths
    file_paths += re.findall(r'(?:^|\s)([a-zA-Z][\w/\\.-]*\.\w{1,5})(?:\s|$|,|\))', hint_text, re.MULTILINE)
    
    if not file_paths:
        return []
    
    wrong_ext_files = []
    for fp in file_paths:
        # Extract extension
        ext_match = re.search(r'(\.\w+)$', fp)
        if ext_match:
            ext = ext_match.group(1).lower()
            # Only flag if it's a known code extension but wrong for this repo
            if ext in ALL_KNOWN_EXTENSIONS and ext not in valid_exts:
                # Allow common config files
                config_exts = {".json", ".yml", ".yaml", ".toml", ".xml", ".md", ".txt", ".cfg", ".ini", ".env"}
                if ext not in config_exts:
                    wrong_ext_files.append(f"{fp} (has {ext}, repo uses {valid_exts})")
    
    if wrong_ext_files:
        failures.append(f"Wrong file extensions: {'; '.join(wrong_ext_files[:3])}")
    
    return failures


def _check_boilerplate(hint_text: str) -> list:
    """Detect generic/boilerplate verb phrases."""
    failures = []
    matches = []
    
    hint_lower = hint_text.lower()
    for pattern in BANNED_PHRASES:
        found = re.findall(pattern, hint_lower)
        matches.extend(found)
    
    if len(matches) >= 2:
        failures.append(f"Boilerplate detected ({len(matches)} generic phrases: {', '.join(matches[:4])})")
    
    return failures


def _check_specificity(hint_text: str) -> list:
    """Check for concrete technical identifiers (class names, function calls, etc.)."""
    failures = []
    
    # Count concrete identifiers:
    # - PascalCase words (class names): ResponseHandler, UserService
    pascal_case = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', hint_text)
    # - Function calls: foo(), bar.baz()
    function_calls = re.findall(r'\b\w+\.\w+\(', hint_text) + re.findall(r'\b\w+\(\)', hint_text)
    # - File paths with directories
    file_paths = re.findall(r'\b\w+/\w+', hint_text)
    # - camelCase identifiers
    camel_case = re.findall(r'\b[a-z]+[A-Z][a-z]+\w*\b', hint_text)
    # - snake_case identifiers (2+ segments)
    snake_case = re.findall(r'\b[a-z]+_[a-z]+(?:_[a-z]+)*\b', hint_text)
    
    total_identifiers = len(set(pascal_case + function_calls + camel_case)) + min(len(file_paths), 3)
    
    if total_identifiers < 2:
        failures.append(f"Low specificity: only {total_identifiers} concrete identifiers found")
    
    return failures
