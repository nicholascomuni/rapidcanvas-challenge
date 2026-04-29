"""Thin pytest wrapper for the evaluation harness."""

import asyncio
import os
import pytest
from tests.eval.eval_runner import run

BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")


@pytest.mark.asyncio
def test_eval_harness():
    exit_code = asyncio.run(run(BASE_URL))
    assert exit_code == 0, "Evaluation harness failed — check eval_report.json for details"
