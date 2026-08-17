"""
GitNova Pre-Filter Layer
========================
Hybrid gate that runs BEFORE DeBERTa (zero cost — pure Python, no model calls).
Rejects issues that are epics, rants, proposals, non-code tasks, or too vague.
"""

import re

# --- REJECTION KEYWORD LISTS ---

TITLE_REJECT_KEYWORDS = [
    "proposal", "rfc", "roadmap", "rewrite", "overhaul",
    "migration", "redesign", "epic", "umbrella", "tracking issue",
    "meta:", "meta-issue", "discussion:", "brainstorm",
]

NON_CODE_LABELS = {
    "question", "discussion", "wontfix", "invalid", "duplicate",
    "won't fix", "stale", "needs triage", "needs info",
}

DOCS_ONLY_LABELS = {
    "documentation", "docs", "typo", "doc", "documentation-only",
}


def pre_filter_issue(title: str, body: str, labels: list = None) -> dict:
    """
    Run all pre-filter rules on an issue.
    
    Returns:
        {
            "pass": True/False,
            "reason": "reason string" or None
        }
    """
    labels = labels or []
    label_names = {lbl.get("name", "").lower() if isinstance(lbl, dict) else str(lbl).lower() for lbl in labels}
    
    # Rule 1: Title keyword rejection
    title_lower = title.lower().strip()
    for keyword in TITLE_REJECT_KEYWORDS:
        if keyword in title_lower:
            return _reject(f"Title contains banned keyword: '{keyword}'", rule_id="TITLE_BANNED_KEYWORD")
    
    # Rule 2: ALL-CAPS detection (>70% uppercase)
    alpha_chars = [c for c in title if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.70 and len(alpha_chars) > 5:
            return _reject(f"Title is {upper_ratio:.0%} uppercase (screaming/rant)", rule_id="ALL_CAPS_TITLE")
    
    # Rule 3: Short body rejection (<20 words)
    body_clean = (body or "").strip()
    word_count = len(body_clean.split())
    if word_count < 20:
        return _reject(f"Body too short ({word_count} words, minimum 20)", rule_id="BODY_TOO_SHORT")
    
    # Rule 4: Rant tone detection (≥3 exclamation marks + ≥2 all-caps words)
    exclamation_count = body_clean.count("!")
    allcaps_words = [w for w in body_clean.split() if w.isupper() and len(w) > 2]
    if exclamation_count >= 3 and len(allcaps_words) >= 2:
        return _reject(f"Rant tone detected ({exclamation_count} exclamations, {len(allcaps_words)} all-caps words)", rule_id="RANT_TONE")
    
    # Rule 5: Documentation-only detection
    if label_names and label_names.issubset(DOCS_ONLY_LABELS):
        # Only reject if body has no code-file references
        code_file_pattern = r'\b\w+\.(py|js|ts|tsx|jsx|java|go|rs|rb|swift|kt|c|cpp|h|yml|yaml|json|toml)\b'
        if not re.search(code_file_pattern, body_clean):
            return _reject("Documentation-only issue (no code files referenced)", rule_id="DOCS_ONLY")
    
    # Rule 6: Epic / tracking issue detection (≥5 pending tasks or tracking keywords with checklist)
    unchecked_count = len(re.findall(r'- \[ \]', body_clean))
    total_checklist = len(re.findall(r'- \[[ xX]\]', body_clean))
    if unchecked_count >= 5 or (total_checklist >= 5 and any(w in title_lower for w in ["tracking", "epic", "roadmap", "todo", "umbrella", "meta", "v2", "v3"])):
        return _reject(f"Epic/umbrella tracking issue ({total_checklist} checklist items, {unchecked_count} pending)", rule_id="EPIC_TRACKING_ISSUE")
    
    # Rule 7: Non-code task labels
    if label_names and label_names.issubset(NON_CODE_LABELS):
        return _reject(f"Non-code task (labels: {', '.join(label_names)})", rule_id="NON_CODE_LABELS")
    
    # Rule 8: Feature request that's really an architecture proposal
    architecture_signals = [
        "new architecture", "complete rewrite", "from scratch",
        "ground up", "v2", "v3", "next generation", "next-gen",
        "re-architect", "rearchitect",
    ]
    body_lower = body_clean.lower()
    arch_hits = sum(1 for s in architecture_signals if s in body_lower)
    if arch_hits >= 2:
        return _reject(f"Architecture proposal ({arch_hits} architecture signals)", rule_id="ARCHITECTURE_PROPOSAL")
    
    return {"pass": True, "reason": None, "rule_id": None}


def pre_filter_issue_from_csv(title: str, ai_hint: str) -> dict:
    """
    Lightweight pre-filter for retroactive CSV cleaning.
    Uses title + ai_hint (since we don't have the original body in the CSV).
    """
    title_lower = title.lower().strip()
    
    # Rule 1: Title keyword rejection
    for keyword in TITLE_REJECT_KEYWORDS:
        if keyword in title_lower:
            return _reject(f"Title contains banned keyword: '{keyword}'", rule_id="TITLE_BANNED_KEYWORD")
    
    # Rule 2: ALL-CAPS title
    alpha_chars = [c for c in title if c.isalpha()]
    if alpha_chars:
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        if upper_ratio > 0.70 and len(alpha_chars) > 5:
            return _reject(f"Title is {upper_ratio:.0%} uppercase", rule_id="ALL_CAPS_TITLE")
    
    # Rule 3: Epic patterns in title
    epic_patterns = [
        r'\[roadmap\]', r'\[epic\]', r'\[tracking\]', r'\[meta\]',
    ]
    for pattern in epic_patterns:
        if re.search(pattern, title_lower):
            return _reject(f"Epic/tracking pattern in title", rule_id="EPIC_TRACKING_PATTERN")
    
    return {"pass": True, "reason": None, "rule_id": None}


def _reject(reason: str, rule_id: str = "PREFILTER_REJECT") -> dict:
    return {"pass": False, "reason": reason, "rule_id": rule_id}

