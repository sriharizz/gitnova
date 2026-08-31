import os
import sys
import shutil
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[3]
docs_arch = repo_root / "docs" / "architecture"
docs_maint = repo_root / "docs" / "maintenance"
docs_arch.mkdir(parents=True, exist_ok=True)
docs_maint.mkdir(parents=True, exist_ok=True)

# 1. Move root-level docs into docs/
root_moves = {
    "GITNOVA_COMPLETE_HANDBOOK_v4.2.md": docs_arch / "GITNOVA_COMPLETE_HANDBOOK_v4.2.md",
    "GITNOVA_v4.2_PRODUCT_VISION_SHIFT.md": docs_arch / "GITNOVA_v4.2_PRODUCT_VISION_SHIFT.md",
    "gitnova_complete_architecture.md": docs_arch / "gitnova_complete_architecture.md",
    "final_plan.md": docs_maint / "final_plan.md",
    "LATER.md": docs_maint / "LATER.md"
}

print("Moving root-level documentation into docs/...")
for filename, dest_path in root_moves.items():
    src_path = repo_root / filename
    if src_path.exists():
        shutil.move(str(src_path), str(dest_path))
        print(f"  Moved: {filename} -> {dest_path.relative_to(repo_root)}")

# 2. Update .gitignore to include interview_evidence/
gitignore_path = repo_root / ".gitignore"
with open(gitignore_path, "r", encoding="utf-8") as f:
    gi_content = f.read()

if "interview_evidence" not in gi_content:
    gi_content += "\n# --- Local Interview Evidence & Demonstration Packs (Kept Local) ---\ninterview_evidence/\n/interview_evidence/\n"
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(gi_content)
    print("Updated .gitignore with interview_evidence/ rule.")
else:
    print(".gitignore already has interview_evidence/ rule.")

print("Root cleanup script finished.")
