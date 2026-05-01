from evaluation.metrics import (
    bullet_count_score,
    bullets_context_similarity,
    citation_score,
    search_query_similarity,
)


# --- citation_score ---

def test_citation_has_sources():
    assert citation_score(["https://example.com", "https://other.com"]) == 1.0


def test_citation_no_sources():
    assert citation_score([]) == 0.0


# --- bullet_count_score ---

def test_bullet_count_in_range():
    assert bullet_count_score(3, 3, 5) == 1.0
    assert bullet_count_score(5, 3, 5) == 1.0


def test_bullet_count_out_of_range():
    assert bullet_count_score(2, 3, 5) == 0.0
    assert bullet_count_score(6, 3, 5) == 0.0


# --- bullets_context_similarity ---

def test_context_similarity_returns_none_when_empty():
    assert bullets_context_similarity(["some bullet"], "") is None
    assert bullets_context_similarity(["some bullet"], "   ") is None


# --- search_query_similarity ---

def test_query_similarity_returns_none_when_no_expected():
    assert search_query_similarity(["some query"], []) is None
