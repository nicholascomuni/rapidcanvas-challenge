"""Pytest wrapper for the evaluation harness — owns the pass/fail thresholds."""

import os
import pytest
from evaluation.eval_runner import run_eval

BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")

# Embedding-based thresholds (cosine similarity, 0–1)
EXPLANATION_SIM_THRESHOLD = 0.55
CONTEXT_SIM_THRESHOLD = 0.45      # only cases with non-empty relevant_context count
SEARCH_QUERY_SIM_THRESHOLD = 0.45  # only cases with expected_search_queries count

# Structural thresholds
CITATION_THRESHOLD = 0.8

# LLM-judge threshold (normalized mean of 7 dimensions, 0–1)
JUDGE_SCORE_THRESHOLD = 0.5


@pytest.mark.asyncio
async def test_eval_explanation_similarity():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("bullets_explanation_similarity", 0)
    assert actual >= EXPLANATION_SIM_THRESHOLD, (
        f"Mean explanation similarity {actual:.3f} below threshold {EXPLANATION_SIM_THRESHOLD}"
        " — check evaluation/eval_report.json"
    )


@pytest.mark.asyncio
async def test_eval_context_similarity():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("bullets_context_similarity")
    if actual is None:
        pytest.skip("No cases with non-empty relevant_context")
    assert actual >= CONTEXT_SIM_THRESHOLD, (
        f"Mean context similarity {actual:.3f} below threshold {CONTEXT_SIM_THRESHOLD}"
        " — check evaluation/eval_report.json"
    )


@pytest.mark.asyncio
async def test_eval_search_query_similarity():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("search_query_similarity")
    if actual is None:
        pytest.skip("No cases with expected_search_queries")
    assert actual >= SEARCH_QUERY_SIM_THRESHOLD, (
        f"Mean search query similarity {actual:.3f} below threshold {SEARCH_QUERY_SIM_THRESHOLD}"
        " — check evaluation/eval_report.json"
    )


@pytest.mark.asyncio
async def test_eval_citation():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("citation", 0)
    assert actual >= CITATION_THRESHOLD, (
        f"Mean citation score {actual:.3f} below threshold {CITATION_THRESHOLD}"
        " — check evaluation/eval_report.json"
    )


@pytest.mark.asyncio
async def test_eval_judge_score():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("judge_score", 0)
    assert actual >= JUDGE_SCORE_THRESHOLD, (
        f"Mean judge score {actual:.3f} below threshold {JUDGE_SCORE_THRESHOLD}"
        " — check evaluation/eval_report.json"
    )
