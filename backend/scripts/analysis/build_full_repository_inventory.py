import os
import sys
import csv
import json
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[3]
docs_maint = repo_root / "docs" / "maintenance"
docs_maint.mkdir(parents=True, exist_ok=True)

# Scan files
ignore_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", ".gemini", "coverage"}

all_files = []
for p in repo_root.rglob("*"):
    if p.is_file():
        parts = p.relative_to(repo_root).parts
        if any(ign in parts for ign in ignore_dirs):
            continue
        all_files.append(p.relative_to(repo_root))

print(f"Total non-ignored files: {len(all_files)}")

# Build lookup text from GHA workflows, backend/app, frontend/src
gha_text = ""
for gha in (repo_root / ".github" / "workflows").glob("*.yml"):
    gha_text += gha.read_text(encoding="utf-8", errors="ignore") + "\n"

inventory_rows = []

for rel_path in all_files:
    posix_path = str(rel_path).replace("\\", "/")
    stem = rel_path.stem
    name = rel_path.name
    ext = rel_path.suffix.lower()

    category = "UNKNOWN"
    if posix_path.startswith("backend/app/"):
        category = "PRODUCTION"
    elif posix_path.startswith("frontend/src/"):
        category = "PRODUCTION"
    elif posix_path.startswith(".github/workflows/"):
        category = "DEPLOYMENT"
    elif posix_path.startswith("backend/tests/") or posix_path.startswith("tests/"):
        category = "TEST"
    elif posix_path.startswith("docs/"):
        category = "DOCUMENTATION"
    elif posix_path.startswith("interview_evidence/"):
        category = "ANALYSIS"
    elif posix_path.startswith("backend/data/dataset_collection/"):
        category = "EXPERIMENT"
    elif posix_path.startswith("backend/data/qlora_shadow_demo/"):
        category = "EXPERIMENT"
    elif posix_path.startswith("backend/scripts/"):
        if "eval" in posix_path or "golden" in posix_path:
            category = "EVALUATION"
        elif "qlora" in posix_path or "dataset" in posix_path:
            category = "EXPERIMENT"
        elif "audit" in posix_path or "analysis" in posix_path or "inspect" in posix_path or "extract" in posix_path:
            category = "ANALYSIS"
        elif "migration" in posix_path or "index" in posix_path:
            category = "PRODUCTION"
        else:
            category = "ANALYSIS"
    elif ext in (".md", ".txt") and not posix_path.startswith("backend/app/"):
        category = "DOCUMENTATION"
    elif ext in (".json", ".csv", ".jsonl"):
        category = "DATASET"
    elif posix_path in ("Dockerfile", "docker-compose.yml", "vercel.json", ".env.example", "render.yaml"):
        category = "DEPLOYMENT"
    elif posix_path in ("package.json", "requirements.txt", "pyproject.toml", "vite.config.ts", "tsconfig.json"):
        category = "PRODUCTION"

    is_called_in_gha = name in gha_text
    is_imported = posix_path.startswith("backend/app/") or posix_path.startswith("frontend/src/")
    
    safe_to_move = True
    safe_to_delete = False
    
    if category in ("PRODUCTION", "TEST", "DEPLOYMENT") or is_called_in_gha or is_imported:
        safe_to_move = False
        safe_to_delete = False
    elif category == "ANALYSIS" and not is_called_in_gha:
        if name.startswith("temp_") or name.startswith("scratch_") or name == "run_server.py":
            safe_to_delete = True

    row = {
        "file_path": posix_path,
        "category": category,
        "extension": ext,
        "is_imported_in_prod": is_imported,
        "is_called_in_gha": is_called_in_gha,
        "is_referenced_in_docs": posix_path.startswith("docs/"),
        "safe_to_move": safe_to_move,
        "safe_to_delete": safe_to_delete
    }
    inventory_rows.append(row)

# Write CSV
csv_path = docs_maint / "repository_inventory.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(inventory_rows[0].keys()))
    writer.writeheader()
    writer.writerows(inventory_rows)

# Write Markdown
md_path = docs_maint / "repository_inventory.md"
category_counts = {}
for r in inventory_rows:
    c = r["category"]
    category_counts[c] = category_counts.get(c, 0) + 1

md_content = f"""# GitNova — Full Repository Inventory Report

**Inventory Date:** 2026-08-31  
**Total Non-Ignored Files:** {len(inventory_rows)}  

---

## 1. File Count by Functional Category

| Category | File Count | Percentage | Description |
| :--- | :--- | :--- | :--- |
"""

for cat, cnt in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
    pct = cnt / len(inventory_rows) * 100
    md_content += f"| **{cat}** | {cnt} | {pct:.1f}% | Files categorized as {cat} |\n"

md_content += f"""
---

## 2. Top-Level Directory Inventory Summary

- **`backend/app/`**: Core production FastAPI backend application (Strictly Locked).
- **`frontend/src/`**: Core production React 19 + Vite frontend (Strictly Locked).
- **`backend/scripts/`**: Engineering tooling (Evaluation, Dataset, Analysis, Maintenance).
- **`backend/data/`**: Production datasets, benchmarks, QLoRA adapter model.
- **`docs/`**: Long-term documentation and architectural guides.
- **`interview_evidence/`**: Comprehensive interview evidence packs and dossiers.
- **`.github/workflows/`**: Production CI/CD and scheduled ingestion automation.

---

## 3. Detailed Inventory Reference
Full line-by-line file metadata is recorded in [`repository_inventory.csv`](file:///c:/gitNova/docs/maintenance/repository_inventory.csv).
"""

with open(md_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"✅ Generated {md_path} and {csv_path}")
