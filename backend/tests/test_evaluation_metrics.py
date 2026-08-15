"""
GitNova v4.2 — Evaluation Metrics Unit & Regression Tests

Regression tests for:
  1. Out-of-bounds cases (zero ground-truth fix files) return None (N/A), not 1.0.
  2. File-level deduplication preserves correct first-appearance file ranks.
  3. Mean Reciprocal Rank (MRR) aggregation precision excluding None values.
"""

import pytest
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


class TestOutOfBoundsRegression:

    def test_out_of_bounds_recall_returns_none(self):
        retrieved = ["generate-readme.js", "LICENSE"]
        gt = []  # Zero ground truth primary fix files (out-of-bounds)
        recall = calculate_recall_at_k(retrieved, gt, k=10)
        assert recall is None

    def test_recall_at_k_exact_match(self):
        retrieved = ["start.js", "help/start.txt", "README.md"]
        gt = ["start.js"]
        recall = calculate_recall_at_k(retrieved, gt, k=10)
        assert recall == 1.0

    def test_precision_at_k_calculation(self):
        retrieved = ["start.js", "help/start.txt", "README.md"]
        gt = ["start.js"]
        precision = calculate_precision_at_k(retrieved, gt, k=10)
        assert precision == pytest.approx(1.0 / 3.0)

    def test_out_of_bounds_hit_returns_none(self):
        retrieved = ["generate-readme.js", "LICENSE"]
        gt = []
        hit = calculate_hit_at_k(retrieved, gt, k=10)
        assert hit is None

    def test_out_of_bounds_mrr_returns_none(self):
        retrieved = ["generate-readme.js", "LICENSE"]
        gt = []
        mrr = calculate_mrr_at_k(retrieved, gt, k=10)
        assert mrr is None

    def test_out_of_bounds_rank_returns_none(self):
        retrieved = ["generate-readme.js", "LICENSE"]
        gt = []
        rank = get_first_match_rank(retrieved, gt, k=10)
        assert rank is None

    def test_mean_mrr_excludes_none_scores(self):
        # 3 queries: 1.0 (Rank 1), 0.5 (Rank 2), and None (Out-of-bounds)
        rr_scores = [1.0, 0.5, None]
        mean_mrr = calculate_mean_mrr(rr_scores)
        # Mean should be (1.0 + 0.5) / 2 = 0.75, ignoring None
        assert mean_mrr == pytest.approx(0.75)


class TestDeduplicationRegression:

    def test_deduplication_preserves_order(self):
        retrieved = ["start.js", "help/start.txt", "start.js", "README.md", "help/start.txt"]
        deduped = deduplicate_retrieved_files(retrieved)
        assert deduped == ["start.js", "help/start.txt", "README.md"]

    def test_deduplicated_file_rank_calculation(self):
        # Multiple chunks from "help/start.txt" at ranks 1, 2, 3 before target "start.js"
        retrieved = [
            "help/start.txt",
            "help/start.txt",
            "help/start.txt",
            "start.js"
        ]
        gt = ["start.js"]
        
        # Unique file ranks:
        # 1. "help/start.txt"
        # 2. "start.js" -> Should be Rank #2 (RR = 0.5), not Rank #4!
        
        rank = get_first_match_rank(retrieved, gt, k=10)
        rr = calculate_mrr_at_k(retrieved, gt, k=10)

        assert rank == 2
        assert rr == pytest.approx(0.5)


class TestMRRCalculationPrecision:

    def test_exact_mrr_sum_aggregation(self):
        # 9 in-bounds queries with known reciprocal ranks:
        # GT-1: 0.25 (Rank 4)
        # GT-2: 1.00 (Rank 1)
        # GT-3: 1.00 (Rank 1)
        # GT-4: 0.3333333333333333 (Rank 3)
        # GT-5: 1.00 (Rank 1)
        # GT-6: 1.00 (Rank 1)
        # GT-7: 1.00 (Rank 1)
        # GT-8: 1.00 (Rank 1)
        # GT-9: 0.50 (Rank 2)
        # GT-10: None (Out of bounds)
        
        rr_scores = [0.25, 1.0, 1.0, (1.0 / 3.0), 1.0, 1.0, 1.0, 1.0, 0.5, None]
        
        valid_scores = [s for s in rr_scores if s is not None]
        assert len(valid_scores) == 9
        
        expected_mean = (0.25 + 1.0 + 1.0 + (1.0 / 3.0) + 1.0 + 1.0 + 1.0 + 1.0 + 0.5) / 9.0
        calculated_mean = calculate_mean_mrr(rr_scores)
        
        assert calculated_mean == pytest.approx(expected_mean)
        assert calculated_mean == pytest.approx(0.787037, abs=1e-5)


class TestGradedRelevance:

    def test_primary_fix_file_relevance(self):
        rel = calculate_file_relevance("start.js", ["start.js"], ["help/start.txt"])
        assert rel == PRIMARY_FIX_WEIGHT

    def test_supporting_file_relevance(self):
        rel = calculate_file_relevance("help/start.txt", ["start.js"], ["help/start.txt"])
        assert rel == SUPPORTING_WEIGHT

    def test_irrelevant_file_relevance(self):
        rel = calculate_file_relevance("random.py", ["start.js"], ["help/start.txt"])
        assert rel == IRRELEVANT_WEIGHT
