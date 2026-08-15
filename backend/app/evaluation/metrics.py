"""
GitNova v4.2 — Evaluation Metrics Engine (Corrected Version)

Provides standardized mathematical formulations for Information Retrieval (IR),
code citation grounding, solution actionability, and latency percentiles.

Corrected Metrics Rules:
  - Deduplicates retrieved chunks by file_path before computing file-level Recall@K, Hit@K, and MRR@K.
  - Returns None for out-of-bounds cases (zero ground-truth primary_fix_files) for Recall@K, Hit@K, and MRR@K.
  - Excludes out-of-bounds cases from average Recall, Hit Rate, and Mean MRR aggregations.
  - Evaluates out-of-bounds cases separately using short-circuit safety metrics.
"""

import math
from typing import List, Dict, Any, Set, Tuple, Optional


# ── 1. Three-Tier Relevance Grading ──────────────────────────────────────────

PRIMARY_FIX_WEIGHT = 1.0
SUPPORTING_WEIGHT = 0.5
IRRELEVANT_WEIGHT = 0.0


def calculate_file_relevance(
    file_path: str,
    primary_fix_files: List[str],
    supporting_files: List[str]
) -> float:
    """
    Computes three-tier graded relevance score for a retrieved file.
      - 1.0 if file_path matches any primary_fix_files
      - 0.5 if file_path matches any supporting_files
      - 0.0 if file_path is irrelevant
    """
    file_norm = file_path.strip()
    
    for prim in primary_fix_files:
        prim_norm = prim.strip()
        if file_norm == prim_norm or file_norm.endswith('/' + prim_norm) or prim_norm.endswith('/' + file_norm):
            return PRIMARY_FIX_WEIGHT

    for supp in supporting_files:
        supp_norm = supp.strip()
        if file_norm == supp_norm or file_norm.endswith('/' + supp_norm) or supp_norm.endswith('/' + file_norm):
            return SUPPORTING_WEIGHT

    return IRRELEVANT_WEIGHT


# ── 2. File-Level Deduplication ──────────────────────────────────────────────

def deduplicate_retrieved_files(retrieved_files: List[str]) -> List[str]:
    """
    Deduplicates a list of retrieved file paths while strictly preserving order of first appearance.
    """
    seen = set()
    deduped = []
    for f in retrieved_files:
        f_norm = f.strip()
        if f_norm and f_norm not in seen:
            seen.add(f_norm)
            deduped.append(f_norm)
    return deduped


# ── 3. Information Retrieval (IR) Metrics ────────────────────────────────────

def calculate_recall_at_k(
    retrieved_files: List[str],
    ground_truth_fix_files: List[str],
    k: int = 10
) -> Optional[float]:
    """
    Computes Recall@K for file-level retrieval results against ground truth fix files.
    Returns None for out-of-bounds cases (zero ground-truth fix files).
    """
    if not ground_truth_fix_files:
        return None

    deduped_files = deduplicate_retrieved_files(retrieved_files)[:k]
    top_k_files = set(deduped_files)
    matched_count = 0

    for gt in ground_truth_fix_files:
        gt_norm = gt.strip()
        if any(ret == gt_norm or ret.endswith('/' + gt_norm) or gt_norm.endswith('/' + ret) for ret in top_k_files):
            matched_count += 1

    return float(matched_count) / float(len(ground_truth_fix_files))


def calculate_precision_at_k(
    retrieved_files: List[str],
    ground_truth_fix_files: List[str],
    k: int = 10
) -> Optional[float]:
    """
    Computes Precision@K for file-level retrieval results against ground truth fix files.
    Precision@K = |Retrieved Top-K Files ∩ Ground Truth Fix Files| / min(k, len(retrieved_files))
    Returns None for out-of-bounds cases (zero ground-truth fix files).
    """
    if not ground_truth_fix_files:
        return None

    deduped_files = deduplicate_retrieved_files(retrieved_files)[:k]
    if not deduped_files:
        return 0.0

    top_k_files = set(deduped_files)
    matched_count = 0

    for gt in ground_truth_fix_files:
        gt_norm = gt.strip()
        if any(ret == gt_norm or ret.endswith('/' + gt_norm) or gt_norm.endswith('/' + ret) for ret in top_k_files):
            matched_count += 1

    return float(matched_count) / float(len(deduped_files))


def calculate_hit_at_k(
    retrieved_files: List[str],
    ground_truth_fix_files: List[str],
    k: int = 10
) -> Optional[float]:
    """
    Computes Hit@K (binary 1.0 or 0.0) indicating whether at least one primary fix file was retrieved in Top-K.
    Returns None for out-of-bounds cases (zero ground-truth fix files).
    """
    if not ground_truth_fix_files:
        return None

    deduped_files = deduplicate_retrieved_files(retrieved_files)[:k]
    top_k_files = set(deduped_files)

    for gt in ground_truth_fix_files:
        gt_norm = gt.strip()
        if any(ret == gt_norm or ret.endswith('/' + gt_norm) or gt_norm.endswith('/' + ret) for ret in top_k_files):
            return 1.0

    return 0.0


def calculate_mrr_at_k(
    retrieved_files: List[str],
    ground_truth_fix_files: List[str],
    k: int = 10
) -> Optional[float]:
    """
    Computes Reciprocal Rank (RR@K) for a single query using deduplicated unique file ranks (1-indexed).
    Returns None for out-of-bounds cases (zero ground-truth fix files).
    Returns 0.0 if not found in Top-K.
    """
    if not ground_truth_fix_files:
        return None

    deduped_files = deduplicate_retrieved_files(retrieved_files)[:k]
    gt_set = {gt.strip() for gt in ground_truth_fix_files}

    for idx, ret in enumerate(deduped_files, 1):
        ret_norm = ret.strip()
        if any(ret_norm == gt or ret_norm.endswith('/' + gt) or gt.endswith('/' + ret_norm) for gt in gt_set):
            return 1.0 / float(idx)

    return 0.0


def calculate_mean_mrr(rr_scores: List[Optional[float]]) -> float:
    """
    Computes Mean Reciprocal Rank (MRR) strictly across valid non-None in-bounds queries.
    """
    valid_scores = [s for s in rr_scores if s is not None]
    if not valid_scores:
        return 0.0
    return sum(valid_scores) / float(len(valid_scores))


def get_first_match_rank(
    retrieved_files: List[str],
    ground_truth_fix_files: List[str],
    k: int = 10
) -> Optional[int]:
    """
    Returns 1-based unique file rank of the first matching primary fix file in Top-K, or None if not found/oob.
    """
    if not ground_truth_fix_files:
        return None

    deduped_files = deduplicate_retrieved_files(retrieved_files)[:k]
    gt_set = {gt.strip() for gt in ground_truth_fix_files}

    for idx, ret in enumerate(deduped_files, 1):
        ret_norm = ret.strip()
        if any(ret_norm == gt or ret_norm.endswith('/' + gt) or gt.endswith('/' + ret_norm) for gt in gt_set):
            return idx

    return None


# ── 4. Grounding & Safety Metrics ────────────────────────────────────────────

def calculate_citation_verification_rate(
    total_citations: int,
    verified_citations: int
) -> float:
    """
    Computes Citation Verification Rate (CVR) as percentage of response file citations verified in retrieved context.
    """
    if total_citations == 0:
        return 100.0
    return (float(verified_citations) / float(total_citations)) * 100.0


def calculate_hallucination_rate(
    citation_verification_rate: float
) -> float:
    """
    Computes Hallucination Rate (HR) as 100.0 - CVR. Target SLA = 0.0%.
    """
    return max(0.0, 100.0 - citation_verification_rate)


def calculate_short_circuit_accuracy(
    total_out_of_bounds_queries: int,
    correct_insufficient_evidence_count: int
) -> float:
    """Computes accuracy of short-circuiting out-of-bounds or thin context queries."""
    if total_out_of_bounds_queries == 0:
        return 100.0
    return (float(correct_insufficient_evidence_count) / float(total_out_of_bounds_queries)) * 100.0


def calculate_solution_actionability_score(
    step_count: int,
    has_target_file_badges: bool,
    min_steps: int = 3
) -> float:
    """
    Computes Solution Actionability Score (SAS) as 1.0 or 0.0.
    """
    if step_count >= min_steps and has_target_file_badges:
        return 1.0
    return 0.0


# ── 5. Performance Metrics ───────────────────────────────────────────────────

def calculate_percentile_latency(
    latencies_ms: List[int],
    percentile: float = 50.0
) -> int:
    """
    Computes P50 or P95 percentile wall-clock latency in milliseconds.
    """
    if not latencies_ms:
        return 0

    sorted_lat = sorted(latencies_ms)
    k = (len(sorted_lat) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return int(sorted_lat[int(k)])

    d0 = sorted_lat[int(f)] * (c - k)
    d1 = sorted_lat[int(c)] * (k - f)
    return int(round(d0 + d1))
