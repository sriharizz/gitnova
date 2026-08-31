"""
GitNova Pre-Filter & Language Suitability Layer
================================================
High-recall, deterministic gate that runs BEFORE expensive AST indexing,
RAG retrieval, and Gemini LLM reasoning.

Responsibilities:
1. Hard Exclusions: PRs, closed issues, empty records, bot noise.
2. Soft Quality Guardrails: Extremely short bodies, epic checklists, rant tones.
3. Language Suitability: Deterministic Unicode script analysis rejecting clearly non-English content
   (CJK, Cyrillic, Arabic) from the primary English feed, while preserving English issues with code,
   stack traces, URLs, and technical identifiers.
"""

import re
from typing import Any, Dict, List, Optional

# --- REJECTION KEYWORD LISTS ---

TITLE_REJECT_KEYWORDS = [
    "roadmap", "rewrite", "overhaul", "migration", "redesign",
    "epic", "umbrella", "tracking issue", "meta-issue",
]

# Obvious Bot & System Authors / Patterns
BOT_AUTHORS = {
    "dependabot[bot]", "dependabot", "renovate[bot]", "renovate",
    "stale[bot]", "stale", "codecov[bot]", "codecov",
    "github-actions[bot]", "github-actions", "snyk-bot", "snyk",
    "greenkeeper[bot]", "greenkeeper", "semantic-release-bot",
}

BOT_TITLE_PATTERNS = [
    r"^Bumps?\s+[\w\.\-]+(?:\s+from\s+[\w\.\-]+)?\s+to\s+[\w\.\-]+",
    r"^chore\(deps(?:-dev)?\):",
    r"^\[Snyk\]\s+(?:Security|Fix|Upgrade)",
    r"^This issue has been automatically marked as stale",
]

# Non-code labels that indicate closed/wontfix status
CLOSED_OR_INVALID_LABELS = {
    "wontfix", "won't fix", "invalid", "duplicate", "stale",
}

# Unicode Script Pattern for Non-Latin Detection
# CJK: \u4e00-\u9fff, \u3400-\u4dbf, \u3040-\u30ff (Hiragana/Katakana), \uac00-\ud7af (Hangul)
# Cyrillic: \u0400-\u04ff
# Arabic: \u0600-\u06ff
# Devanagari: \u0900-\u097f
NON_LATIN_SCRIPT_PATTERN = re.compile(
    r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff\u0900-\u097f]'
)


def clean_prose_text(text: str) -> str:
    """
    Strips code blocks, inline code, URLs, stack traces, and formatting
    to isolate human prose for language suitability analysis.
    """
    if not text:
        return ""
    # Strip markdown code blocks (fenced ```...```)
    cleaned = re.sub(r'```[\s\S]*?```', ' ', text)
    # Strip inline code (`...`)
    cleaned = re.sub(r'`[^`]*`', ' ', cleaned)
    # Strip URLs
    cleaned = re.sub(r'https?://\S+', ' ', cleaned)
    # Strip stack trace lines
    cleaned = re.sub(r'(?:File\s+".*",\s+line\s+\d+|at\s+[\w\.\$/\\]+\([\w\.:\s]+\)|Traceback\s+\(most\s+recent\s+call\s+last\):)', ' ', cleaned)
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    return cleaned


def is_clearly_non_english(title: str, body: str) -> tuple[bool, str]:
    """
    Deterministically evaluates whether the issue is predominantly written in a non-Latin script (CJK, Cyrillic, Arabic).
    Uses prose character ratio after stripping code, URLs, and stack traces.
    Threshold: >20% non-Latin script characters in title or body prose.
    """
    # Check title prose
    title_prose = clean_prose_text(title)
    title_letters = [c for c in title_prose if c.isalpha()]
    if title_letters:
        non_latin_count = len(NON_LATIN_SCRIPT_PATTERN.findall(title_prose))
        ratio = non_latin_count / len(title_letters)
        if ratio > 0.20 and non_latin_count >= 2:
            return True, f"Title contains {ratio:.0%} non-Latin script characters"

    # Check body prose
    body_prose = clean_prose_text(body)
    body_letters = [c for c in body_prose if c.isalpha()]
    if body_letters and len(body_letters) > 10:
        non_latin_count = len(NON_LATIN_SCRIPT_PATTERN.findall(body_prose))
        ratio = non_latin_count / len(body_letters)
        if ratio > 0.20 and non_latin_count >= 5:
            return True, f"Body contains {ratio:.0%} non-Latin script characters"

    return False, ""


def pre_filter_issue(
    title: str,
    body: str,
    labels: list = None,
    author: Optional[str] = None,
    state: str = "open",
    is_pr: bool = False,
    html_url: str = "",
) -> dict:
    """
    Run high-recall deterministic pre-filter rules on an issue.

    Returns:
        {
            "pass": bool,
            "eligible": bool,
            "stage": "issue_pre_filter",
            "rule_id": str or None,
            "reason": str or None,
            "reason_codes": list[str],
        }
    """
    labels = labels or []
    label_names = {lbl.get("name", "").lower() if isinstance(lbl, dict) else str(lbl).lower() for lbl in labels}
    title_clean = (title or "").strip()
    body_clean = (body or "").strip()

    # Rule 1: Pull request exclusion
    if is_pr or "/pull/" in (html_url or ""):
        return _reject("Record is a pull request, not an issue", rule_id="PULL_REQUEST")

    # Rule 2: Closed issue exclusion
    if state and state.lower() == "closed":
        return _reject("Issue is closed (open contribution required)", rule_id="CLOSED_ISSUE")

    # Rule 3: Empty title exclusion
    if not title_clean:
        return _reject("Issue title is empty", rule_id="EMPTY_TITLE")

    # Rule 4: Completely empty body exclusion
    if not body_clean or len(body_clean.strip()) < 5:
        return _reject("Issue body is empty or too short", rule_id="EMPTY_BODY")

    # Rule 5: Non-English script suitability (CJK, Cyrillic, Arabic)
    non_en, non_en_reason = is_clearly_non_english(title_clean, body_clean)
    if non_en:
        return _reject(f"Non-English content: {non_en_reason}", rule_id="NON_ENGLISH_CONTENT")

    # Rule 6: Short English body (< 5 words)
    words = body_clean.split()
    if len(words) < 5 and len(body_clean) < 30:
        return _reject(f"Issue body too short ({len(words)} words, minimum 5)", rule_id="EMPTY_BODY")

    # Rule 7: Bot / System generated content
    author_lower = (author or "").lower().strip()
    if author_lower in BOT_AUTHORS or "[bot]" in author_lower:
        return _reject(f"Automated bot submission by '{author}'", rule_id="BOT_OR_SYSTEM_CONTENT")
    
    for bot_pattern in BOT_TITLE_PATTERNS:
        if re.search(bot_pattern, title_clean, re.IGNORECASE):
            return _reject("Automated bot or dependency bump issue", rule_id="BOT_OR_SYSTEM_CONTENT")

    # Rule 7: Title banned keyword rejection (Epics, Roadmap, Rewrite)
    title_lower = title_clean.lower()
    for keyword in TITLE_REJECT_KEYWORDS:
        if keyword in title_lower:
            return _reject(f"Title contains banned keyword: '{keyword}'", rule_id="TITLE_BANNED_KEYWORD")

    # Rule 8: ALL-CAPS title screaming/rant detection (>70% uppercase)
    alpha_chars = [c for c in title_clean if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.70 and len(alpha_chars) > 5:
            return _reject(f"Title is {upper_ratio:.0%} uppercase (screaming/rant)", rule_id="ALL_CAPS_TITLE")

    # Rule 9: Rant tone detection (≥3 exclamation marks + ≥2 all-caps words)
    exclamation_count = body_clean.count("!")
    allcaps_words = [w for w in words if w.isupper() and len(w) > 2]
    if exclamation_count >= 3 and len(allcaps_words) >= 2:
        return _reject(f"Rant tone detected ({exclamation_count} exclamations, {len(allcaps_words)} all-caps words)", rule_id="RANT_TONE")

    # Rule 10: Epic / tracking checklist overflow (≥5 pending sub-tasks)
    unchecked_count = len(re.findall(r'- \[ \]', body_clean))
    total_checklist = len(re.findall(r'- \[[ xX]\]', body_clean))
    if unchecked_count >= 5 or (total_checklist >= 5 and any(w in title_lower for w in ["tracking", "epic", "roadmap", "todo", "umbrella", "meta", "v2", "v3"])):
        return _reject(f"Epic/umbrella tracking issue ({total_checklist} checklist items, {unchecked_count} pending)", rule_id="EPIC_TRACKING_ISSUE")

    # Rule 11: Closed / Invalid labels
    if label_names and label_names.issubset(CLOSED_OR_INVALID_LABELS):
        return _reject(f"Invalid issue label status ({', '.join(label_names)})", rule_id="NON_CODE_LABELS")

    # Rule 12: Broad architecture overhaul request
    architecture_signals = [
        "complete rewrite", "rewrite from scratch",
        "ground up rewrite", "next generation overhaul",
        "complete re-architect",
    ]
    body_lower = body_clean.lower()
    arch_hits = sum(1 for s in architecture_signals if s in body_lower)
    if arch_hits >= 2:
        return _reject(f"Architecture overhaul proposal ({arch_hits} signals)", rule_id="ARCHITECTURE_PROPOSAL")

    return {
        "pass": True,
        "eligible": True,
        "stage": "issue_pre_filter",
        "rule_id": None,
        "reason": None,
        "reason_codes": [],
    }


def pre_filter_issue_from_csv(title: str, ai_hint: str) -> dict:
    """
    Lightweight pre-filter for retroactive CSV cleaning.
    Uses title + ai_hint (since we don't have the original body in the CSV).
    """
    title_clean = (title or "").strip()
    title_lower = title_clean.lower()

    if not title_clean:
        return _reject("Issue title is empty", rule_id="EMPTY_TITLE")

    non_en, non_en_reason = is_clearly_non_english(title_clean, ai_hint or "")
    if non_en:
        return _reject(f"Non-English content: {non_en_reason}", rule_id="NON_ENGLISH_CONTENT")

    for keyword in TITLE_REJECT_KEYWORDS:
        if keyword in title_lower:
            return _reject(f"Title contains banned keyword: '{keyword}'", rule_id="TITLE_BANNED_KEYWORD")

    alpha_chars = [c for c in title_clean if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.70 and len(alpha_chars) > 5:
            return _reject(f"Title is {upper_ratio:.0%} uppercase", rule_id="ALL_CAPS_TITLE")

    epic_patterns = [
        r'\[roadmap\]', r'\[epic\]', r'\[tracking\]', r'\[meta\]',
    ]
    for pattern in epic_patterns:
        if re.search(pattern, title_lower):
            return _reject("Epic/tracking pattern in title", rule_id="EPIC_TRACKING_PATTERN")

    return {
        "pass": True,
        "eligible": True,
        "stage": "issue_pre_filter",
        "rule_id": None,
        "reason": None,
        "reason_codes": [],
    }


def _reject(reason: str, rule_id: str = "PREFILTER_REJECT") -> dict:
    return {
        "pass": False,
        "eligible": False,
        "stage": "issue_pre_filter",
        "rule_id": rule_id,
        "reason": reason,
        "reason_codes": [rule_id],
    }
