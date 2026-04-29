from tests.eval.metrics import (
    bullet_count_score,
    citation_score,
    coverage_score,
    hallucination_score,
)


def test_coverage_full():
    assert coverage_score(["The Ralph Wiggum technique uses bash loops"], ["Ralph Wiggum", "bash"]) == 1.0


def test_coverage_partial():
    score = coverage_score(["Only mentions Ralph Wiggum"], ["Ralph Wiggum", "bash loops"])
    assert score == 0.5


def test_coverage_empty_topics():
    assert coverage_score(["anything"], []) == 1.0


def test_citation_all_cited():
    bullets = [{"citations": [{"index": 1}]}, {"citations": [{"index": 2}]}]
    assert citation_score(bullets) == 1.0


def test_citation_none_cited():
    bullets = [{"citations": []}, {"citations": []}]
    assert citation_score(bullets) == 0.0


def test_hallucination_clean():
    assert hallucination_score(["OpenAI funded this"], ["invented by Google"]) == 1.0


def test_hallucination_detected():
    assert hallucination_score(["invented by Google in 2020"], ["invented by Google"]) == 0.0


def test_bullet_count_in_range():
    assert bullet_count_score(3, 3, 5) == 1.0
    assert bullet_count_score(5, 3, 5) == 1.0


def test_bullet_count_out_of_range():
    assert bullet_count_score(2, 3, 5) == 0.0
    assert bullet_count_score(6, 3, 5) == 0.0
