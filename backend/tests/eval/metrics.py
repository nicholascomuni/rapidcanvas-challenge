"""
Scoring functions for the evaluation harness.
All functions are pure and take simple Python types so they can be unit tested easily.
"""

from __future__ import annotations


_STOP_WORDS = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "is", "are", "was", "were", "about"}


def coverage_score(bullet_texts: list[str], expected_topics: list[str]) -> float:
    """
    Fraction of expected_topics covered in the bullets.
    A topic is covered if either:
      - the full phrase appears as a substring (exact match), OR
      - every significant word in the topic appears somewhere in the bullets
        (handles paraphrasing like "judicial nominees" vs "Trump judicial nominees").
    Returns 1.0 if expected_topics is empty.
    """
    if not expected_topics:
        return 1.0

    combined = " ".join(bullet_texts).lower()

    def _is_covered(topic: str) -> bool:
        t = topic.lower()
        if t in combined:
            return True
        words = [w for w in t.split() if w not in _STOP_WORDS and len(w) > 2]
        return bool(words) and all(w in combined for w in words)

    covered = sum(1 for topic in expected_topics if _is_covered(topic))
    return covered / len(expected_topics)


def citation_score(sources: list[str]) -> float:
    """
    1.0 if at least one source URL was returned, 0.0 otherwise.
    The new agent returns sources as a flat list of URLs; having any source
    means the response is grounded in web evidence.
    """
    return 1.0 if sources else 0.0


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
