"""
Scoring functions for the evaluation harness.
All functions are pure and take simple Python types so they can be unit tested easily.
"""

from __future__ import annotations


def coverage_score(bullet_texts: list[str], expected_topics: list[str]) -> float:
    """
    Fraction of expected_topics that appear (case-insensitively) in any bullet.
    Returns 1.0 if expected_topics is empty (nothing to cover = trivially satisfied).
    """
    if not expected_topics:
        return 1.0

    combined = " ".join(bullet_texts).lower()
    covered = sum(1 for topic in expected_topics if topic.lower() in combined)
    return covered / len(expected_topics)


def citation_score(bullets: list[dict]) -> float:
    """
    Fraction of bullets that contain at least one citation.
    bullets: list of dicts with key 'citations' (list).
    Returns 1.0 if bullets list is empty.
    """
    if not bullets:
        return 1.0
    cited = sum(1 for b in bullets if b.get("citations"))
    return cited / len(bullets)


def hallucination_score(bullet_texts: list[str], must_not_contain: list[str]) -> float:
    """
    Returns 1.0 (clean) if none of must_not_contain strings appear in any bullet.
    Returns 0.0 (hallucination detected) if any forbidden string is found.
    """
    if not must_not_contain:
        return 1.0
    combined = " ".join(bullet_texts).lower()
    for forbidden in must_not_contain:
        if forbidden.lower() in combined:
            return 0.0
    return 1.0


def bullet_count_score(num_bullets: int, min_bullets: int, max_bullets: int) -> float:
    """1.0 if count is within [min_bullets, max_bullets], else 0.0."""
    return 1.0 if min_bullets <= num_bullets <= max_bullets else 0.0


def aggregate_scores(results: list[dict]) -> dict:
    """Compute mean across all cases for each metric."""
    if not results:
        return {}
    keys = ["coverage", "citation", "hallucination", "bullet_count", "judge_score"]
    return {
        k: round(sum(r.get(k, 0) for r in results) / len(results), 3)
        for k in keys
        if any(k in r for r in results)
    }
