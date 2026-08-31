import os
import sys
import shutil
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

repo_root = Path(__file__).resolve().parents[3]
scripts_dir = repo_root / "backend" / "scripts"

eval_dir = scripts_dir / "evaluation"
dataset_dir = scripts_dir / "dataset"
analysis_dir = scripts_dir / "analysis"
maint_dir = scripts_dir / "maintenance"

for d in (eval_dir, dataset_dir, analysis_dir, maint_dir):
    d.mkdir(parents=True, exist_ok=True)

# Mapping of file -> destination folder
moves = {
    # Evaluation
    "run_longitudinal_evaluation.py": eval_dir,
    "run_10_eval_batch.py": eval_dir,
    "evaluate_gitnova_model.py": eval_dir,
    "evaluate_v4_5_final_8repos.py": eval_dir,
    "evaluate_v4_5_quality.py": eval_dir,
    "measure_llm_reliability.py": eval_dir,
    "run_v4_5_three_issues_quality_gate.py": eval_dir,

    # Dataset
    "collect_finetuning_dataset.py": dataset_dir,
    "run_gitnova_qlora_experiment.py": dataset_dir,

    # Maintenance
    "reindex_repos.py": maint_dir,
    "clean_database_v2.py": maint_dir,
    "clean_supabase.py": maint_dir,
    "export_supabase.py": maint_dir,
    "run_canonical_pilot_ingestion.py": maint_dir,
    "run_canonical_real_issue_trace.py": maint_dir,
    "run_final_pre_deployment_validation.py": maint_dir,
    "run_single_issue_ingestion.py": maint_dir,
    "seed_live_published_issues.py": maint_dir,
    "verify_index_coverage_regression.py": maint_dir,
    "verify_post_migration_16.py": maint_dir,
    "verify_production_pipeline_dry_run.py": maint_dir,

    # Analysis
    "analyze_diagnostic_results.py": analysis_dir,
    "analyze_longitudinal_buckets.py": analysis_dir,
    "audit_9_grounding_failures.py": analysis_dir,
    "audit_and_expand_real_issues.py": analysis_dir,
    "audit_bucket_a_deep_dive.py": analysis_dir,
    "audit_evaluation_model.py": analysis_dir,
    "audit_frontend_demo_issues.py": analysis_dir,
    "build_interview_evidence_pack.py": analysis_dir,
    "export_issues_dossier.py": analysis_dir,
    "extract_10_audit_cases.py": analysis_dir,
    "extract_log_snippets.py": analysis_dir,
    "finalize_bucket_a_audit.py": analysis_dir,
    "finalize_trace_from_jsonl.py": analysis_dir,
    "find_3_new_real_issues.py": analysis_dir,
    "generate_full_10_issue_report.py": analysis_dir,
    "generate_interview_master_artifacts.py": analysis_dir,
    "inspect_longitudinal_hits.py": analysis_dir,
    "inspect_rotation.py": analysis_dir,
    "prepare_audit_update.py": analysis_dir,
    "run_diagnostic_40_experiment.py": analysis_dir,
    "verify_trace_csv.py": analysis_dir
}

print("Executing script reorganization...")
for filename, dest_folder in moves.items():
    src_file = scripts_dir / filename
    if src_file.exists() and src_file.is_file():
        dest_file = dest_folder / filename
        shutil.move(str(src_file), str(dest_file))
        print(f"  Moved: scripts/{filename} -> scripts/{dest_folder.name}/{filename}")

# Create root shim for reindex_repos.py for backward compatibility with GitHub Actions reindex.yml
shim_content = """# Backward compatibility shim for GitHub Actions and existing tooling
import sys
from pathlib import Path

target_script = Path(__file__).resolve().parent / "maintenance" / "reindex_repos.py"
if target_script.exists():
    with open(target_script, "r", encoding="utf-8") as f:
        code = compile(f.read(), str(target_script), "exec")
        exec(code, globals())
"""
with open(scripts_dir / "reindex_repos.py", "w", encoding="utf-8") as f:
    f.write(shim_content)
print("  Created backward compatibility shim: backend/scripts/reindex_repos.py")

# Remove obsolete untracked root scratch file backend/run_server.py
scratch_file = repo_root / "backend" / "run_server.py"
if scratch_file.exists():
    scratch_file.unlink()
    print("  Removed obsolete scratch file: backend/run_server.py")

# Move FRONTEND_5_ISSUES_EVALUATION.md to docs/evaluation/
f5_file = repo_root / "FRONTEND_5_ISSUES_EVALUATION.md"
docs_eval = repo_root / "docs" / "evaluation"
docs_eval.mkdir(parents=True, exist_ok=True)
if f5_file.exists():
    shutil.move(str(f5_file), str(docs_eval / "FRONTEND_5_ISSUES_EVALUATION.md"))
    print("  Moved FRONTEND_5_ISSUES_EVALUATION.md -> docs/evaluation/FRONTEND_5_ISSUES_EVALUATION.md")

print("✅ Repository cleanup execution completed successfully.")
