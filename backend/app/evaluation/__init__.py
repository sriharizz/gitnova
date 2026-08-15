"""
GitNova v4.2 — Evaluation Module
"""

from app.evaluation.metrics import (
    calculate_file_relevance,
    deduplicate_retrieved_files,
    calculate_recall_at_k,
    calculate_precision_at_k,
    calculate_hit_at_k,
    calculate_mrr_at_k,
    calculate_mean_mrr,
    get_first_match_rank,
    calculate_citation_verification_rate,
    calculate_hallucination_rate,
    calculate_short_circuit_accuracy,
    calculate_solution_actionability_score,
    calculate_percentile_latency,
    PRIMARY_FIX_WEIGHT,
    SUPPORTING_WEIGHT,
    IRRELEVANT_WEIGHT,
)

__all__ = [
    "calculate_file_relevance",
    "deduplicate_retrieved_files",
    "calculate_recall_at_k",
    "calculate_precision_at_k",
    "calculate_hit_at_k",
    "calculate_mrr_at_k",
    "calculate_mean_mrr",
    "get_first_match_rank",
    "calculate_citation_verification_rate",
    "calculate_hallucination_rate",
    "calculate_short_circuit_accuracy",
    "calculate_solution_actionability_score",
    "calculate_percentile_latency",
    "PRIMARY_FIX_WEIGHT",
    "SUPPORTING_WEIGHT",
    "IRRELEVANT_WEIGHT",
]
