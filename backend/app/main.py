import os
import requests
import json
import sys
from supabase import create_client
from dotenv import load_dotenv

# --- IMPORTS ---
# We use absolute imports assuming the app is run as a module
from app.ml.transformer_brain import predict_difficulty_with_transformer
from app.pipeline.bot import evaluate_and_enrich

load_dotenv()

# --- ⚙️ CONFIGURATION: THE FULL MEGA LIST (PRESERVED) ---
INTERESTS = {
    "Frontend": [
        "facebook/react", "shadcn-ui/ui", "vercel/next.js", 
        "tailwindlabs/tailwindcss", "mui/material-ui", "sveltejs/svelte",
        "vuejs/core", "remix-run/remix", "solidjs/solid", "withastro/astro",
        "freeCodeCamp/freeCodeCamp", "storybookjs/storybook", "appsmithorg/appsmith"
    ],
    "Machine Learning": [
        "pytorch/pytorch", "huggingface/transformers", "langchain-ai/langchain", 
        "tensorflow/tensorflow", "karpathy/nanoGPT", "openai/whisper",
        "microsoft/DeepSpeed", "ray-project/ray", "huggingface/diffusers",
        "scikit-learn/scikit-learn", "keras-team/keras", "streamlit/streamlit"
    ],
    "Backend": [
        "fastapi/fastapi", "django/django", "nestjs/nest", "expressjs/express",
        "tiangolo/sqlmodel", "pallets/flask", "rails/rails", "laravel/laravel",
        "strapi/strapi", "go-gorm/gorm", "RocketChat/Rocket.Chat", 
        "supabase/supabase", "redis/redis"
    ],
    "DevOps": [
        "microsoft/vscode", "docker/cli", "kubernetes/kubernetes", 
        "ansible/ansible", "prometheus/prometheus", "grafana/grafana",
        "hashicorp/terraform", "jenkinsci/jenkins", "gitlabhq/gitlabhq",
        "elastic/elasticsearch", "moby/moby"
    ],
    "Data Science": [
        "pandas-dev/pandas", "apache/spark", "apache/arrow", 
        "plotly/plotly.py", "matplotlib/matplotlib", "ydataai/ydata-profiling",
        "seleniumhq/selenium", "scrapy/scrapy"
    ],
    "Mobile": [
        "flutter/flutter", "facebook/react-native", "ionic-team/ionic-framework", 
        "expo/expo", "airbnb/lottie-android", "square/retrofit", 
        "realm/realm-swift", "skylot/jadx"
    ]
}

# 🚦 SAFE MODE SETTINGS
DRY_RUN = False              # Set True to test without DB writes
FETCH_PER_REPO = 30          # GitHub fetching depth
LOCAL_MIN_CONFIDENCE = 0.30  # DeBERTa Pass/Fail Threshold
CLOUD_SELECTION_LIMIT = 15   # Max issues to send to Groq per batch (Cost Control)

# Init Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("❌ CRITICAL: Supabase credentials missing from .env")

supabase = create_client(supabase_url, supabase_key)

# --- JANITOR ---
def clean_closed_issues():
    """Removes issues from Supabase if they are now closed on GitHub."""
    if DRY_RUN: return
    print("\n🧹 JANITOR: Checking for closed issues...")
    try:
        response = supabase.table("issues").select("id, repo_name, url").eq("status", "PUBLISHED").execute()
        db_issues = response.data
        
        token = os.getenv("GITHUB_TOKEN")
        headers = {"Authorization": f"token {token}"} if token else {}
        
        closed_count = 0
        for issue in db_issues:
            # Construct API URL from HTML URL
            api_url = issue['url'].replace("github.com", "api.github.com/repos")
            try:
                r = requests.get(api_url, headers=headers, timeout=5)
                if r.status_code == 200:
                    gh_data = r.json()
                    if gh_data.get('state') == 'closed':
                        supabase.table("issues").delete().eq("id", issue['id']).execute()
                        print(f"   🗑️ Removed closed issue: {issue['repo_name']} #{issue['id']}")
                        closed_count += 1
            except Exception:
                continue
                
        print(f"   ✨ Janitor finished. Removed {closed_count} closed issues.\n")
    except Exception as e:
        print(f"   ⚠️ Janitor Error: {e}")

# --- PIPELINE ---
def run_pipeline():
    print(f"🚀 STARTING GITNOVA ENGINE")
    print(f"📝 MODE: {'DRY RUN' if DRY_RUN else 'PRODUCTION'}")
    print(f"🔒 SAFE MODE ACTIVE: Limiting Judge to top {CLOUD_SELECTION_LIMIT} candidates.")

    clean_closed_issues()
    
    for category, repos in INTERESTS.items():
        print(f"\n🌍 CATEGORY: {category}")
        candidates = []
        
        # A. HUNT (GitHub API)
        for repo in repos:
            try:
                url = f"https://api.github.com/repos/{repo}/issues?state=open&sort=created&per_page={FETCH_PER_REPO}"
                
                token = os.getenv("GITHUB_TOKEN")
                headers = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json"
                } if token else {}

                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    issues = resp.json()
                    # Sanity check: Ensure we got a list
                    if not isinstance(issues, list): continue
                    print(f"   ✅ {repo}: Scanned {len(issues)} issues")
                elif resp.status_code == 403:
                    print(f"   🛑 {repo}: RATE LIMIT HIT (403).")
                    continue
                else:
                    print(f"   ⚠️ {repo}: Status {resp.status_code}")
                    continue
                
                for issue in issues:
                    if 'pull_request' in issue: continue 
                    
                    # B. FILTER (Local DeBERTa)
                    text = f"{issue['title']} {issue['body']}"
                    analysis = predict_difficulty_with_transformer(text)
                    
                    # Filter out obvious non-starters immediately
                    if analysis['score'] < LOCAL_MIN_CONFIDENCE: 
                        continue
                    
                    candidates.append({"data": issue, "analysis": analysis, "repo": repo})

            except Exception as e:
                print(f"   ❌ Error scanning {repo}: {e}")

        # C. SORT & PRIORITIZE
        if not candidates:
            print("   💤 No suitable candidates found.")
            continue

        candidates.sort(key=lambda x: x['analysis']['score'], reverse=True)
        top_picks = candidates[:CLOUD_SELECTION_LIMIT] 
        
        print(f"   💎 Sending {len(top_picks)} Best Candidates to The Judge...")

        # D. JUDGE (Cloud Llama)
        for item in top_picks:
            issue = item['data']
            safe_body = issue.get('body') or "" 
            
            ai_response = evaluate_and_enrich(
                issue['title'], 
                safe_body, 
                item['repo'], 
                item['analysis']['difficulty']
            )
            
            if ai_response:
                try:
                    judgement = json.loads(ai_response)
                    if judgement.get('verified_difficulty') == "Reject": 
                        print(f"      🚫 Rejected: {issue['title'][:20]}...")
                        continue
                        
                    final_record = {
                        "id": issue['id'],
                        "title": issue['title'],
                        "repo_name": item['repo'],
                        "difficulty": judgement.get('verified_difficulty', item['analysis']['difficulty']),
                        "ai_score": item['analysis']['score'],
                        "ai_hint": judgement.get('hint', "No hint available."),
                        "category": category,
                        "url": issue['html_url'],
                        "status": "PUBLISHED",
                        "created_at": issue['created_at']
                    }
                    
                    if DRY_RUN:
                        print(f"      📝 [Dry Run] Would save: {issue['title'][:30]}...")
                    else:
                        # Upsert checks "id" to avoid duplicates
                        supabase.table("issues").upsert(final_record).execute()
                        print(f"      ✅ Published: {issue['title'][:30]}...")
                        
                except Exception as e:
                    print(f"      ⚠️ Integration Error: {e}")

if __name__ == "__main__":
    run_pipeline()