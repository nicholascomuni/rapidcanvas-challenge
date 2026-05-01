"""Pytest wrapper for the evaluation harness — owns the pass/fail thresholds."""

import os
import pytest
from tests.eval.eval_runner import run_eval

BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")

COVERAGE_THRESHOLD = 0.6
CITATION_THRESHOLD = 0.6
HALLUCINATION_THRESHOLD = 1.0  # must be clean


@pytest.mark.asyncio
async def test_eval_coverage():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("coverage", 0)
    assert actual >= COVERAGE_THRESHOLD, (
        f"Mean coverage {actual:.3f} below threshold {COVERAGE_THRESHOLD} — check eval_report.json"
    )


@pytest.mark.asyncio
async def test_eval_citation():
    report = await run_eval(BASE_URL)
    agg = report["aggregate"]
    actual = agg.get("citation", 0)
    assert actual >= CITATION_THRESHOLD, (
        f"Mean citation {actual:.3f} below threshold {CITATION_THRESHOLD} — check eval_report.json"
    )


@pytest.mark.asyncio
async def test_eval_no_hallucinations():
    report = await run_eval(BASE_URL)
    active = [r for r in report["cases"] if not r.get("skipped")]
    failing = [r["id"] for r in active if r.get("hallucination", 1.0) < HALLUCINATION_THRESHOLD]
    assert not failing, f"Hallucinations detected in cases: {failing} — check eval_report.json"
