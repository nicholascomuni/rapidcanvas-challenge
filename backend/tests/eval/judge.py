"""LLM-as-judge scorer using GPT-4o-mini."""

from __future__ import annotations
import json

from openai import AsyncOpenAI

from core.config import get_settings

_JUDGE_SYSTEM = """\
You are a strict, impartial evaluator of AI-generated explanations of social media posts.
Your job is to identify weaknesses, not to reward effort. Be critical and use the full 1–5 scale.
A score of 4 or 5 must be genuinely earned. Scores of 3 should be your default for adequate-but-unremarkable work.

Rate the explanation on these four dimensions:

1. accuracy (1–5)
   1 = contains factual errors or contradicts the sources
   2 = mostly unverifiable claims, sources barely support the bullets
   3 = claims are plausible but not well-supported by the provided sources
   4 = claims are clearly supported by the sources with only minor gaps
   5 = every claim is directly traceable to a source, no unsupported assertions

2. relevance (1–5)
   1 = bullets explain something unrelated to the post
   2 = tangentially related but misses the core point of the post
   3 = covers the general topic but not the specific angle or nuance of this post
   4 = clearly explains this specific post with only minor off-topic content
   5 = every bullet directly addresses why this particular post is noteworthy

3. clarity (1–5)
   1 = confusing, jargon-heavy, or unreadable
   2 = understandable but awkward or overly technical for a general audience
   3 = readable but generic phrasing, could apply to any post on this topic
   4 = well-written and specific, a non-expert would understand immediately
   5 = exceptionally clear, precise, and engaging

4. context (1–5)
   1 = no background added beyond what the post already says
   2 = minimal context, mostly restates the post
   3 = adds some background but misses key context (who, why it matters, history)
   4 = solid background on the key people, events, or concepts involved
   5 = rich, specific context that makes the post fully understandable to an outsider

Scoring rules:
- Do NOT give 5 unless the explanation is genuinely exceptional in that dimension.
- Do NOT give 4 just because there are no obvious errors — mediocre work scores 3.
- A score of 1 or 2 is appropriate whenever the explanation fails its basic purpose.
- Penalise vague filler bullets ("This post relates to an ongoing debate...") heavily on relevance and context.

Return ONLY valid JSON:
{
  "accuracy": <1-5>,
  "relevance": <1-5>,
  "clarity": <1-5>,
  "context": <1-5>,
  "reasoning": "<two or three sentences identifying the main strengths AND weaknesses>"
}"""


def make_judge_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)


async def llm_judge(
    post_text: str,
    bullets: list[dict],
    sources: list[str],
    client: AsyncOpenAI | None = None,
) -> dict:
    """
    Returns a dict with accuracy, relevance, clarity, context (1-5 each),
    reasoning (str), and judge_score (mean of the four dimensions, 0-1 normalized).
    Pass a pre-built client to reuse the HTTP connection across multiple calls.
    """
    if client is None:
        client = make_judge_client()

    bullet_block = "\n".join(f"- {b.get('text', '')}" for b in bullets)
    source_block = "\n".join(f"[Source {i+1}] {url}" for i, url in enumerate(sources))

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
        print(f"  [ERROR] llm_judge failed: {exc}")
        return {"error": str(exc), "judge_score": 0.0}

    scores = [data.get(k, 0) for k in ("accuracy", "relevance", "clarity", "context")]
    valid_scores = [s for s in scores if isinstance(s, (int, float))]
    judge_score = (sum(valid_scores) / (5 * len(valid_scores))) if valid_scores else 0.0

    return {**data, "judge_score": round(judge_score, 3)}
