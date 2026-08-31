from pathlib import Path
import re

log_path = Path("C:/Users/BTSRIHARI/.gemini/antigravity-ide/brain/d15e50be-1442-4351-9234-9651b16cb0a2/.system_generated/tasks/task-3804.log")

with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    log_content = f.read()

issues_to_find = [
    ("brandonp2412/Flexify", "332"),
    ("pallets/click", "3696"),
    ("pallets/click", "3652"),
    ("expressjs/express", "7391"),
    ("Nike-Inc/hal", "142"),
    ("eclipse-apoapsis/ort-server", "5716"),
    ("apache/trafficserver", "13555"),
    ("babalae/better-genshin-impact", "3471"),
    ("brandonp2412/Flexify", "331"),
    ("alibaba/nacos", "15709")
]

for repo, num in issues_to_find:
    print(f"\n=======================================================")
    print(f"ISSUE: {repo} #{num}")
    print(f"=======================================================")
    pattern = rf"(Processing canonical candidate #{num}.*?)(?=(Processing canonical candidate|Processing \[\d+/\d+\]|Extended Janitor|\Z))"
    match = re.search(pattern, log_content, re.DOTALL)
    if match:
        snippet = match.group(1).strip()
        print(snippet[:1500].encode('ascii', errors='replace').decode('ascii'))
    else:
        print("Log section not matched directly, searching candidate mention...")
        lines = [l for l in log_content.splitlines() if f"#{num}" in l or num in l]
        print("\n".join(lines[:10]).encode('ascii', errors='replace').decode('ascii'))
