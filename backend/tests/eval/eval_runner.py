"""
Evaluation harness for the Bluesky Post Explainer.

Usage (standalone — just metrics, no pass/fail):
    cd backend
    python -m tests.eval.eval_runner [--url http://localhost:8000]

Exit code: 0 always when run standalone (metrics only).
To assert against thresholds, use: pytest tests/eval/test_eval.py
"""

from __future__ import annotations

import truststore
truststore.inject_into_ssl()

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

from tests.eval.judge import llm_judge, make_judge_client
from tests.eval.metrics import (
    aggregate_scores,
    bullet_count_score,
    citation_score,
    coverage_score,
    hallucination_score,
)

CASES_PATH = Path(__file__).parent / "cases.json"


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text())


async def call_explain(base_url: str, url: str, cached_text: str) -> dict | None:
    """Hit the running backend; on failure return None."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{base_url}/api/v1/explain",
                json={"url": url},
            )
            resp.raise_for_status()
            data = resp.json()
            data["_live_fetch"] = True
            return data
        except Exception as exc:
            print(f"  [WARN] Live fetch failed for {url}: {exc}")
            return None


async def evaluate_case(base_url: str, case: dict, judge_client) -> dict:
    print(f"\n[{case['id']}] {case['description']}")

    response = await call_explain(base_url, case["url"], case["post_text"])
    live = response is not None

    if not live:
        print("  Skipping: could not reach backend or post unavailable.")
        return {"id": case["id"], "skipped": True, "live_fetch": False}

    bullets = response.get("bullets", [])
    bullet_texts = [b.get("text", "") for b in bullets]
    sources = response.get("sources", [])

    cov = coverage_score(bullet_texts, case.get("expected_topics", []))
    cit = citation_score(sources)
    hal = hallucination_score(bullet_texts, case.get("must_not_contain", []))
    cnt = bullet_count_score(len(bullets), case.get("min_bullets", 1), case.get("max_bullets", 5))

    print(f"  coverage={cov:.2f}  citation={cit:.2f}  hallucination={hal:.2f}  count={cnt:.2f}")

    judge = await llm_judge(case["post_text"], bullets, sources, client=judge_client)
    print(f"  judge_score={judge.get('judge_score', 0):.2f}  reasoning: {judge.get('reasoning', '')}")

    return {
        "id": case["id"],
        "live_fetch": live,
        "skipped": False,
        "coverage": cov,
        "citation": cit,
        "hallucination": hal,
        "bullet_count": cnt,
        "judge_score": judge.get("judge_score", 0.0),
        "judge_detail": judge,
        "bullets": bullet_texts,
    }


async def run_eval(base_url: str) -> dict:
    """Run all eval cases and return raw results. No threshold checking."""
    cases = load_cases()
    judge_client = make_judge_client()
    results = []
    for case in cases:
        result = await evaluate_case(base_url, case, judge_client)
        results.append(result)

    active = [r for r in results if not r.get("skipped")]
    agg = aggregate_scores(active)

    print("\n" + "=" * 60)
    print("AGGREGATE SCORES")
    print("=" * 60)
    for k, v in agg.items():
        print(f"  {k:<20} {v:.3f}")

    report_path = Path(__file__).parent / "eval_report.json"
    report_path.write_text(json.dumps({"aggregate": agg, "cases": results}, indent=2))
    print(f"\nFull report written to: {report_path}")

    return {"aggregate": agg, "cases": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run eval harness (metrics only, no thresholds)")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    asyncio.run(run_eval(args.url))
    sys.exit(0)


if __name__ == "__main__":
    main()
