"""LLM-as-judge scorer using GPT-4o-mini."""

from __future__ import annotations
import json

from openai import AsyncOpenAI

from core.config import get_settings

_JUDGE_SYSTEM = """\
You are an impartial evaluator assessing the quality of an AI-generated explanation of a social media post.

Rate the explanation on the following dimensions (each 1–5):
1. accuracy   – Does the explanation align with verifiable facts from the search sources?
2. relevance  – Does it actually explain the post content, not something tangentially related?
3. clarity    – Are the bullets well-written and easy for a general audience to understand?
4. context    – Does it add genuine background context that helps understand the post?

Return ONLY valid JSON:
{
  "accuracy": <1-5>,
  "relevance": <1-5>,
  "clarity": <1-5>,
  "context": <1-5>,
  "reasoning": "<one or two sentences>"
}"""


async def llm_judge(
    post_text: str,
    bullets: list[dict],
    search_results: list[dict],
) -> dict:
    """
    Returns a dict with accuracy, relevance, clarity, context (1-5 each),
    reasoning (str), and judge_score (mean of the four dimensions, 0-1 normalized).
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    bullet_block = "\n".join(f"- {b.get('text', '')}" for b in bullets)
    source_block = "\n".join(
        f"[Source {i+1}] {r.get('title', '')} — {r.get('url', '')}"
        for i, r in enumerate(search_results)
    )

    user_content = (
        f"POST:\n{post_text}\n\n"
        f"EXPLANATION:\n{bullet_block}\n\n"
        f"SOURCES USED:\n{source_block}"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _JUDGE_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            max_tokens=300,
            temperature=0,
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception as exc:
        return {"error": str(exc), "judge_score": 0.0}

    scores = [data.get(k, 0) for k in ("accuracy", "relevance", "clarity", "context")]
    valid_scores = [s for s in scores if isinstance(s, (int, float))]
    judge_score = (sum(valid_scores) / (5 * len(valid_scores))) if valid_scores else 0.0

    return {**data, "judge_score": round(judge_score, 3)}
