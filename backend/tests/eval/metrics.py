"""
Scoring functions for the evaluation harness.
All functions are pure and take simple Python types so they can be unit tested easily.
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.optimize import linear_sum_assignment

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def bullets_explanation_similarity(bullet_texts: list[str], explanation: str) -> float:
    """Cosine similarity between concatenated bullets and the expected explanation."""
    if not bullet_texts or not explanation:
        return 0.0
    model = _get_model()
    bullets_combined = " ".join(bullet_texts)
    embs = model.encode([bullets_combined, explanation])
    return round(_cosine_similarity(embs[0], embs[1]), 4)


def bullets_context_similarity(bullet_texts: list[str], relevant_context: str) -> float | None:
    """Cosine similarity between concatenated bullets and relevant_context. None if context is empty."""
    if not relevant_context or not relevant_context.strip():
        return None
    if not bullet_texts:
        return 0.0
    model = _get_model()
    bullets_combined = " ".join(bullet_texts)
    embs = model.encode([bullets_combined, relevant_context])
    return round(_cosine_similarity(embs[0], embs[1]), 4)


def search_query_similarity(
    generated_queries: list[str],
    expected_queries: list[str],
) -> float | None:
    """
    Hungarian-matched cosine similarity between generated and expected search queries.
    Penalises over- or under-generation via max(N, M) denominator.
    Returns None if expected_queries is empty.
    """
    if not expected_queries:
        return None
    if not generated_queries:
        return 0.0

    model = _get_model()
    gen_embs = model.encode(generated_queries)
    exp_embs = model.encode(expected_queries)

    n, m = len(generated_queries), len(expected_queries)
    sim_matrix = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            sim_matrix[i, j] = _cosine_similarity(gen_embs[i], exp_embs[j])

    row_ind, col_ind = linear_sum_assignment(-sim_matrix)
    matched_sum = sum(sim_matrix[r, c] for r, c in zip(row_ind, col_ind))
    return round(matched_sum / max(n, m), 4)


def citation_score(sources: list[str]) -> float:
    """1.0 if at least one source URL was returned, 0.0 otherwise."""
    return 1.0 if sources else 0.0


def bullet_count_score(num_bullets: int, min_bullets: int, max_bullets: int) -> float:
    """1.0 if count is within [min_bullets, max_bullets], else 0.0."""
    return 1.0 if min_bullets <= num_bullets <= max_bullets else 0.0


def aggregate_scores(results: list[dict]) -> dict:
    """Compute mean across all cases for each numeric metric, skipping None values."""
    if not results:
        return {}
    keys = [
        "bullets_explanation_similarity",
        "bullets_context_similarity",
        "search_query_similarity",
        "citation",
        "bullet_count",
        "judge_score",
    ]
    out = {}
    for k in keys:
        values = [r[k] for r in results if k in r and r[k] is not None]
        if values:
            out[k] = round(sum(values) / len(values), 3)
    return out
