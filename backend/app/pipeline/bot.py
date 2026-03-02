"""
GitNova LLM Judge — Production Tactical Prompt
===============================================
Rewritten prompt with:
- Banned generic verbs
- Repo grounding injection
- Confidence scoring
- INSUFFICIENT CONTEXT fallback
- File extension enforcement
"""

import os
import time
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ CRITICAL: GROQ_API_KEY is missing from .env")

groq = Groq(api_key=api_key)


SYSTEM_PROMPT = """You are an expert open-source code reviewer. Your job is to verify issue difficulty and produce a CONCRETE tactical plan.

STRICT RULES — VIOLATIONS WILL BE REJECTED:

1. BANNED VERBS — Do NOT use these words in your plan:
   "Review", "Investigate", "Fix", "Test", "Update", "Modify", "Check",
   "Ensure", "Implement", "Research", "Analyze", "Verify", "Examine"
   Instead, use SPECIFIC actions: "Add a null check in", "Rename the method",
   "Insert a new case branch for", "Remove the deprecated call to", "Replace X with Y in"

2. FILE PATHS — Every file path MUST:
   - Use the correct extension for this repository's language
   - Reference directories that plausibly exist in this repository
   - NEVER guess generic paths like src/components/ or src/utils/ unless the repo structure confirms it

3. CONCRETE IDENTIFIERS — You MUST name at least one:
   - Specific class, function, or method name
   - Specific variable, constant, or config key
   - NO generic references like "the relevant function" or "the appropriate module"

4. NO SDLC BOILERPLATE — Do not write generic software lifecycle steps like:
   - "Write comprehensive tests"
   - "Document the changes"
   - "Ensure backward compatibility"
   These are obvious and add zero value.

5. CONFIDENCE — Rate your confidence 0-100:
   - 90-100: You can identify exact files and functions
   - 60-89: You can identify likely files but functions are educated guesses
   - 30-59: You can only guess at the area of code
   - 0-29: Not enough information — output INSUFFICIENT CONTEXT

6. If the issue is vague, a rant, an epic, or asks for architectural redesign:
   Set verified_difficulty to "Reject".
"""


def build_user_prompt(issue_title: str, issue_body: str, repo: str, 
                      initial_difficulty: str, repo_context: dict,
                      retry_feedback: list = None) -> str:
    """Build the user prompt with repo grounding and optional retry feedback."""
    
    grounding = repo_context.get("grounding_block", f"Repository: {repo}")
    valid_exts = repo_context.get("valid_extensions", [])
    ext_note = f"This is a {repo_context.get('language', 'Unknown')} repository. All file paths MUST use {', '.join(valid_exts)} extensions." if valid_exts else ""
    
    prompt = f"""--- REPOSITORY CONTEXT ---
{grounding}
{ext_note}

--- ISSUE ---
Title: {issue_title}
Body: {issue_body[:5000]}

--- TASK ---
Initial difficulty classification: {initial_difficulty}

Verify the difficulty and produce a tactical plan.

Output JSON (strict schema):
{{
    "verified_difficulty": "Novice" | "Apprentice" | "Contributor" | "Reject",
    "reason": "One sentence explaining your classification",
    "confidence": <0-100>,
    "hint": "**🎯 Goal:** [One concrete sentence]\\n\\n**📂 Files:**\\n- `path/to/specific/file.ext`\\n\\n**🔧 Change:**\\n1. In `ClassName.method_name()`, [specific action]\\n2. [Next specific action]"
}}"""

    if retry_feedback:
        feedback_str = "; ".join(retry_feedback)
        prompt += f"""

⚠️ RETRY: Your previous output was rejected for: {feedback_str}
Be MORE SPECIFIC this time. Name exact classes, functions, and file paths. 
Do NOT use any banned verbs. Use the repository context above to ground your file paths."""

    return prompt


def evaluate_and_enrich(issue_title: str, issue_body: str, repo: str, 
                        initial_difficulty: str, repo_context: dict = None,
                        retry_feedback: list = None) -> str:
    """
    Call the LLM to evaluate and enrich an issue.
    
    Args:
        issue_title: The issue's title
        issue_body: The issue's body text
        repo: The repo name (e.g., "facebook/react")
        initial_difficulty: DeBERTa's classification
        repo_context: Dict from get_repo_context() with grounding info
        retry_feedback: Optional list of validation failure reasons (for retries)
    
    Returns:
        JSON string with the LLM's response, or None if all models fail.
    """
    if repo_context is None:
        repo_context = {"grounding_block": f"Repository: {repo}", "valid_extensions": []}
    
    print(f"      ⚡ The Judge is reviewing ({repo})...")
    
    # 🛑 SAFE MODE: RATE LIMIT PROTECTION
    time.sleep(7)

    models = [
        "llama-3.3-70b-versatile",  # Tier 1: Smartest
        "llama-3.1-8b-instant"      # Tier 2: Fastest fallback
    ]
    
    if not issue_body:
        issue_body = "No details provided."

    user_prompt = build_user_prompt(
        issue_title, issue_body, repo, 
        initial_difficulty, repo_context, retry_feedback
    )

    for model in models:
        try:
            completion = groq.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return completion.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                print(f"      ⚠️ Rate Limit hit on {model}. Switching brain... 🔄")
                continue
            else:
                print(f"      ❌ Groq Error ({model}): {e}. Trying next...")
                continue

    print("      🛑 All brains exhausted. Skipping this issue.")
    return None