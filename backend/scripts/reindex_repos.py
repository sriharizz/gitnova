# Backward compatibility shim for GitHub Actions and existing tooling
import sys
from pathlib import Path

target_script = Path(__file__).resolve().parent / "maintenance" / "reindex_repos.py"
if target_script.exists():
    with open(target_script, "r", encoding="utf-8") as f:
        code = compile(f.read(), str(target_script), "exec")
        exec(code, globals())
