"""
Evaluation harness for the Bluesky Post Explainer.

Usage (standalone — just metrics, no pass/fail):
    cd backend
    python -m evaluation.eval_runner [--url http://localhost:8000]

Exit code: 0 always when run standalone (metrics only).
To assert against thresholds, use: pytest tests/test_eval.py
"""

from __future__ import annotations

import truststore
truststore.inject_into_ssl()

import argparse
import asyncio
import json
import sys
import textwrap
from pathlib import Path

import httpx

from evaluation.judge import llm_conclusion, llm_judge, make_judge_client
from evaluation.metrics import (
    aggregate_scores,
    bullet_count_score,
    bullets_context_similarity,
    bullets_explanation_similarity,
    citation_score,
    search_query_similarity,
)

CASES_PATH = Path(__file__).parent / "cases.json"


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text())


async def call_explain(base_url: str, url: str) -> dict | None:
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


_JUDGE_DIMS = (
    "explanation_relevance",
    "faithfulness",
    "groundedness",
    "completeness",
    "clarity",
    "context_relevance",
    "search_query_relevance",
)

_BAR_WIDTH = 20


def _bar(value: float | None, max_value: float = 1.0) -> str:
    """ASCII progress bar, e.g. '████████░░░░░░░░░░░░ 0.42'"""
    if value is None:
        return "N/A"
    filled = round((value / max_value) * _BAR_WIDTH)
    bar = "█" * filled + "░" * (_BAR_WIDTH - filled)
    return f"{bar} {value:.2f}"


def _print_case_summary(case_id: str, metrics: dict, judge: dict) -> None:
    print(f"\n┌─ [{case_id}]")
    print(f"│  Embedding metrics")
    print(f"│    exp_similarity   {_bar(metrics['exp_sim'])}")
    print(f"│    ctx_similarity   {_bar(metrics['ctx_sim'])}")
    print(f"│    query_similarity {_bar(metrics['qry_sim'])}")
    print(f"│    citation         {_bar(metrics['cit'])}")
    print(f"│    bullet_count     {'✓' if metrics['cnt'] == 1.0 else '✗'} ({metrics['n_bullets']} bullets)")
    print(f"│")
    print(f"│  LLM Judge  (overall {_bar(judge.get('judge_score', 0))})")
    for dim in _JUDGE_DIMS:
        entry = judge.get(dim, {})
        if isinstance(entry, dict):
            score = entry.get("score")
            reason = entry.get("reason", "")
        else:
            score = entry
            reason = ""
        bar = _bar(score, max_value=5) if isinstance(score, (int, float)) else "N/A"
        reason_short = (reason[:60] + "…") if len(reason) > 61 else reason
        print(f"│    {dim:<26} {bar}  {reason_short}")
    print(f"└{'─' * 60}")


def _print_aggregate_table(agg: dict) -> None:
    col_w = 35
    print("\n" + "═" * 70)
    print("  AGGREGATE SCORES")
    print("═" * 70)
    print(f"  {'Metric':<{col_w}} {'Bar':<{_BAR_WIDTH + 5}} Score")
    print("  " + "─" * 68)
    for k, v in agg.items():
        print(f"  {k:<{col_w}} {_bar(v, max_value=1.0)}")
    print("═" * 70)


async def evaluate_case(base_url: str, case: dict, judge_client) -> dict:
    print(f"\n  → fetching [{case['id']}] ...", end="", flush=True)

    response = await call_explain(base_url, case["url"])
    if response is None:
        print(" SKIPPED")
        return {"id": case["id"], "skipped": True, "live_fetch": False}
    print(" done")

    bullets = response.get("bullets", [])
    bullet_texts = [b.get("text", b) if isinstance(b, dict) else b for b in bullets]
    sources = response.get("sources", [])
    generated_queries = response.get("search_queries", [])

    explanation = case.get("explanation", "")
    relevant_context = case.get("relevant_context", "")
    expected_queries = case.get("expected_search_queries", [])

    exp_sim = bullets_explanation_similarity(bullet_texts, explanation)
    ctx_sim = bullets_context_similarity(bullet_texts, relevant_context)
    qry_sim = search_query_similarity(generated_queries, expected_queries)
    cit = citation_score(sources)
    cnt = bullet_count_score(len(bullets), case.get("min_bullets", 1), case.get("max_bullets", 5))

    judge = await llm_judge(
        post_text=response.get("post", {}).get("text", ""),
        bullets=bullets,
        sources=sources,
        expected_explanation=explanation,
        relevant_context=relevant_context,
        expected_search_queries=expected_queries,
        generated_search_queries=generated_queries,
        client=judge_client,
    )

    metrics = {"exp_sim": exp_sim, "ctx_sim": ctx_sim, "qry_sim": qry_sim,
               "cit": cit, "cnt": cnt, "n_bullets": len(bullets)}
    _print_case_summary(case["id"], metrics, judge)

    return {
        "id": case["id"],
        "live_fetch": True,
        "skipped": False,
        "bullets_explanation_similarity": exp_sim,
        "bullets_context_similarity": ctx_sim,
        "search_query_similarity": qry_sim,
        "citation": cit,
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
    print(f"Running {len(cases)} eval cases against {base_url} ...")
    for case in cases:
        result = await evaluate_case(base_url, case, judge_client)
        results.append(result)

    active = [r for r in results if not r.get("skipped")]
    agg = aggregate_scores(active)
    _print_aggregate_table(agg)

    print("\n  Generating conclusion...", end="", flush=True)
    conclusion = await llm_conclusion(agg, results, client=judge_client)
    print(" done")
    print("\n" + "═" * 70)
    print("  CONCLUSION")
    print("═" * 70)
    for line in textwrap.wrap(conclusion, width=68):
        print(f"  {line}")
    print("═" * 70)

    report_path = Path(__file__).parent / "eval_report.json"
    report_path.write_text(json.dumps({"aggregate": agg, "cases": results, "conclusion": conclusion}, indent=2))
    print(f"\nFull report → {report_path}")

    return {"aggregate": agg, "cases": results, "conclusion": conclusion}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run eval harness (metrics only, no thresholds)")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    asyncio.run(run_eval(args.url))
    sys.exit(0)


if __name__ == "__main__":
    main()
