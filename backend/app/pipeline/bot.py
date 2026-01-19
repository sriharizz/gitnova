import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("❌ CRITICAL: GROQ_API_KEY is missing from .env")

groq = Groq(api_key=api_key)

def evaluate_and_enrich(issue_title, issue_body, repo, initial_difficulty):
    print(f"      ⚡ The Judge is reviewing ({repo})...")
    
    # 🛑 SAFE MODE: RATE LIMIT PROTECTION
    # 7 seconds sleep guarantees max ~8 calls/min.
    time.sleep(7) 

    models = [
        "llama-3.3-70b-versatile",  # Tier 1: The CEO (Smartest)
        "llama-3.1-8b-instant"      # Tier 2: The Intern (Fastest)
    ]
    
    # Fallback for empty bodies
    if not issue_body: issue_body = "No details provided."

    prompt = f"""
    You are a Senior Maintainer for the repository {repo}.
    
    Task 1: Difficulty Verification.
    - Review the issue. Is '{initial_difficulty}' accurate? 
    - 'Novice': Docs, typos, very simple UI tweaks.
    - 'Apprentice': Standard bug fixes, new features.
    - 'Contributor': Complex architecture, memory leaks, core logic.
    - 'Reject': Vague, spam, or no clear actionable task.
    
    Task 2: The Solution Guide.
    - You MUST identify specific file paths that likely need changes (e.g., `src/components/Button.tsx`).
    - You MUST provide a technical, step-by-step plan.
    
    Issue: {issue_title}
    Body: {issue_body[:6000]}
    
    Output JSON (Strict):
    {{
        "verified_difficulty": "Novice" | "Apprentice" | "Contributor" | "Reject",
        "reason": "1 sentence explanation",
        "hint": "**🎯 Goal:** [One clear sentence]\\n\\n**📂 Likely Files:**\\n- `path/to/file1`\\n- `path/to/file2`\\n\\n**🛠️ Plan:**\\n1. [Step 1]\\n2. [Step 2]"
    }}
    """

    for model in models:
        try:
            completion = groq.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
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