import asyncio
import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from evaluation.eval_runner import evaluate_case, load_cases, run_eval
from evaluation.judge import llm_conclusion, make_judge_client
from evaluation.metrics import aggregate_scores

router = APIRouter(tags=["eval"])

REPORT_PATH = Path(__file__).parent.parent / "evaluation" / "eval_report.json"


@router.get("/eval/report")
async def get_report() -> JSONResponse:
    if not REPORT_PATH.exists():
        return JSONResponse(status_code=404, content={"detail": "No report found. Run evaluation first."})
    return JSONResponse(content=json.loads(REPORT_PATH.read_text()))


@router.post("/eval/run")
async def run_evaluation(body: dict = {}):
    model = body.get("model", "gpt-4o")
    base_url = body.get("base_url", "http://localhost:8000")

    async def event_stream():
        def send(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        cases = load_cases()
        judge_client = make_judge_client()
        results = []

        yield send("start", {"total": len(cases)})

        for i, case in enumerate(cases):
            yield send("case_start", {"id": case["id"], "index": i, "total": len(cases)})

            # Patch the explain call to pass the selected model
            import httpx

            async def call_explain_with_model(url: str) -> dict | None:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    try:
                        resp = await client.post(
                            f"{base_url}/api/v1/explain",
                            json={"url": url, "model": model},
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        data["_live_fetch"] = True
                        return data
                    except Exception as exc:
                        return None

            # Run the case but intercept the HTTP call
            response = await call_explain_with_model(case["url"])

            if response is None:
                result = {"id": case["id"], "skipped": True, "live_fetch": False}
                results.append(result)
                yield send("case_done", {**result})
                continue

            from evaluation.metrics import (
                aggregate_scores,
                bullet_count_score,
                bullets_context_similarity,
                bullets_explanation_similarity,
                citation_score,
                evaluation_score,
                search_query_similarity,
            )
            from evaluation.judge import llm_judge

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

            partial = {
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
                "post": response.get("post"),
            }
            result = {**partial, "evaluation_score": evaluation_score(partial)}
            results.append(result)
            yield send("case_done", result)

        active = [r for r in results if not r.get("skipped")]
        agg = aggregate_scores(active)

        yield send("conclusion_start", {})
        conclusion = await llm_conclusion(agg, results, client=judge_client)

        report = {"aggregate": agg, "cases": results, "conclusion": conclusion}
        REPORT_PATH.write_text(json.dumps(report, indent=2))

        yield send("done", {"aggregate": agg, "conclusion": conclusion})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
