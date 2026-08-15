# backend/app/pipeline/code_retriever.py
import re
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

# ── Local Embeddings (sentence-transformers) ─────────────────────────────────
# Uses jinaai/jina-embeddings-v2-base-code locally via sentence-transformers.
# Same model, 768-dim vectors, zero API cost.
from app.pipeline.embedder import embed_query as _embed_query
# ─────────────────────────────────────────────────────────────────────────────


# Configurable post-RRF information-class weighting constants
INFORMATION_CLASS_WEIGHTS: Dict[str, float] = {
    "SOURCE_CODE": 1.10,
    "DOCUMENTATION": 1.00,
    "CONFIGURATION": 1.00,
    "TESTS": 0.90,
}


def rrf_score(ranks: List[int], k: int = 60) -> float:
    """Computes Reciprocal Rank Fusion score for a list of rank positions."""
    return sum(1.0 / (k + rank) for rank in ranks)


def combine_rrf(
    vector_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
    k: int = 60,
    class_weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Fuses Vector (dense) and Lexical (sparse) retrieval lists using RRF.
    Applies configurable information-class weighting after RRF score computation.
    """
    weights = class_weights if class_weights is not None else INFORMATION_CLASS_WEIGHTS
    candidates: Dict[str, Dict[str, Any]] = {}

    def _extract_candidate(item: Dict[str, Any], rank_idx: int):
        chunk_id = item["chunk_id"]
        if chunk_id in candidates:
            candidates[chunk_id]["ranks"].append(rank_idx + 1)
        else:
            candidates[chunk_id] = {
                "chunk_id": chunk_id,
                "file_path": item["file_path"],
                "symbol_name": item.get("symbol_name"),
                "qualified_symbol_name": item.get("qualified_symbol_name"),
                "symbol_type": item.get("symbol_type"),
                "info_class": item.get("info_class"),
                "contextual_header": item.get("contextual_header"),
                "start_line": item["start_line"],
                "end_line": item["end_line"],
                "content": item["content"],
                "repo_id": item.get("repo_id"),
                "ranks": [rank_idx + 1],
            }

    # Process vector matches
    for rank_idx, item in enumerate(vector_results):
        _extract_candidate(item, rank_idx)

    # Process lexical matches
    for rank_idx, item in enumerate(lexical_results):
        _extract_candidate(item, rank_idx)

    # Calculate final RRF score with post-RRF information class weighting
    fused_list = []
    for candidate in candidates.values():
        raw_score = rrf_score(candidate["ranks"], k)
        info_cls = candidate.get("info_class") or "SOURCE_CODE"
        multiplier = weights.get(info_cls, 1.00)
        final_score = raw_score * multiplier

        candidate_copy = dict(candidate)
        candidate_copy["raw_rrf_score"] = raw_score
        candidate_copy["rrf_score"] = final_score
        fused_list.append(candidate_copy)

    # Sort descending by fused weighted RRF score
    fused_list.sort(key=lambda x: x["rrf_score"], reverse=True)
    return fused_list


def retrieve_code_for_issue(
    supabase_client: Any,
    repo_name: str,
    commit_sha: Optional[str] = None,
    issue_title: str = "",
    issue_body: str = "",
    max_tokens: int = 2500,
    k_candidates: int = 20,
    target_repo_id: Optional[Any] = None,
    mode: str = "hybrid",  # hybrid | vector_only | lexical_only
) -> Tuple[str, List[str]]:
    """
    Main retrieval entry point (v4 adapted).
    Runs Vector + FTS search, merges via RRF, applies metadata filtering & deduplication.
    Returns (formatted_context_string, list_of_retrieved_chunk_ids).
    """
    try:
        query_text = f"{issue_title} {issue_body or ''}".strip()
        if not query_text:
            return "", []

        vector_results = []
        lexical_results = []
        repo_id_str = str(target_repo_id) if target_repo_id else None

        # 1. Vector similarity search
        if mode in {"hybrid", "vector_only"}:
            query_vector = _embed_query(query_text)
            rpc_args = {
                "query_embedding": query_vector,
                "target_repo": repo_name if repo_name else None,
                "target_commit": commit_sha if commit_sha else None,
                "match_count": k_candidates,
                "target_repo_id": repo_id_str,
            }

            vec_resp = supabase_client.rpc("match_chunks_vector", rpc_args).execute()
            vector_results = vec_resp.data or []

        # 2. Lexical keyword search
        if mode in {"hybrid", "lexical_only"}:
            rpc_args = {
                "query_text": query_text[:500],
                "target_repo": repo_name if repo_name else None,
                "target_commit": commit_sha if commit_sha else None,
                "match_count": k_candidates,
                "target_repo_id": repo_id_str,
            }

            lex_resp = supabase_client.rpc("match_chunks_lexical", rpc_args).execute()
            lexical_results = lex_resp.data or []

        if not vector_results and not lexical_results:
            return "", []

        # 3. Fuse via RRF
        if mode == "vector_only":
            fused_results = combine_rrf(vector_results, [])
        elif mode == "lexical_only":
            fused_results = combine_rrf([], lexical_results)
        else:
            fused_results = combine_rrf(vector_results, lexical_results)

        # 4. Deduplicate, concentration guard & token budgeting
        formatted_chunks = []
        retrieved_chunk_ids = []
        token_count = 0
        seen_hashes = set()
        file_counts: Dict[str, int] = {}

        for chunk in fused_results:
            content = chunk["content"]
            c_hash = hash(content)
            if c_hash in seen_hashes:
                continue

            file_path = chunk["file_path"]
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
            if file_counts[file_path] > 3:
                continue

            words = len(content.split())
            est_tokens = int(words * 1.3)
            if token_count + est_tokens > max_tokens and formatted_chunks:
                break

            token_count += est_tokens
            seen_hashes.add(c_hash)
            retrieved_chunk_ids.append(chunk["chunk_id"])

            # Use contextual_header if available (Sprint 6/7 metadata format)
            if chunk.get("contextual_header"):
                header_block = f"--- {chunk['contextual_header']} ---"
            else:
                sym = f" in {chunk['symbol_name']}" if chunk.get("symbol_name") else ""
                header_block = f"--- SOURCE FILE: {file_path} (Lines {chunk['start_line']}-{chunk['end_line']}){sym} ---"

            formatted_chunks.append(f"{header_block}\n{content}\n")

        return "\n".join(formatted_chunks), retrieved_chunk_ids

    except Exception as e:
        print(f"Retrieval Exception for {repo_name}: {e}")
        return "", []


def retrieve_chunks_for_issue(
    supabase_client: Any,
    repo_name: str,
    commit_sha: Optional[str] = None,
    issue_title: str = "",
    issue_body: Optional[str] = None,
    max_tokens: int = 15000,
    k_candidates: int = 20,
    target_repo_id: Optional[Any] = None,
    mode: str = "hybrid",
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Retrieves and returns candidate chunk dictionary objects for Sprint 8 issue grounding.
    """
    try:
        query_text = f"{issue_title} {issue_body or ''}".strip()
        if not query_text:
            return "", []

        vector_results = []
        lexical_results = []
        repo_id_str = str(target_repo_id) if target_repo_id else None

        if mode in {"hybrid", "vector_only"}:
            query_vector = _embed_query(query_text)
            rpc_args = {
                "query_embedding": query_vector,
                "target_repo": repo_name if repo_name else None,
                "target_commit": commit_sha if commit_sha else None,
                "match_count": k_candidates,
                "target_repo_id": repo_id_str,
            }
            vec_resp = supabase_client.rpc("match_chunks_vector", rpc_args).execute()
            vector_results = vec_resp.data or []

        if mode in {"hybrid", "lexical_only"}:
            rpc_args = {
                "query_text": query_text[:500],
                "target_repo": repo_name if repo_name else None,
                "target_commit": commit_sha if commit_sha else None,
                "match_count": k_candidates,
                "target_repo_id": repo_id_str,
            }
            lex_resp = supabase_client.rpc("match_chunks_lexical", rpc_args).execute()
            lexical_results = lex_resp.data or []

        if not vector_results and not lexical_results:
            return "", []

        fused_results = combine_rrf(vector_results, lexical_results, k=60)

        formatted_chunks = []
        selected_chunks = []
        token_count = 0
        seen_hashes = set()
        file_counts: Dict[str, int] = {}

        for chunk in fused_results:
            content = chunk["content"]
            c_hash = hash(content)
            if c_hash in seen_hashes:
                continue

            file_path = chunk["file_path"]
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
            if file_counts[file_path] > 3:
                continue

            words = len(content.split())
            est_tokens = int(words * 1.3)
            if token_count + est_tokens > max_tokens and formatted_chunks:
                break

            token_count += est_tokens
            seen_hashes.add(c_hash)
            selected_chunks.append(chunk)

            if chunk.get("contextual_header"):
                header_block = f"--- {chunk['contextual_header']} ---"
            else:
                sym = f" in {chunk['symbol_name']}" if chunk.get("symbol_name") else ""
                header_block = f"--- SOURCE FILE: {file_path} (Lines {chunk['start_line']}-{chunk['end_line']}){sym} ---"

            formatted_chunks.append(f"{header_block}\n{content}\n")

        return "\n".join(formatted_chunks), selected_chunks

    except Exception as e:
        print(f"Retrieval Exception for {repo_name}: {e}")
        return "", []
