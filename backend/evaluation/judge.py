"""LLM-as-judge scorer using GPT-4o-mini."""

from __future__ import annotations
import json

from openai import AsyncOpenAI

from config import get_settings

_JUDGE_SYSTEM = """\
You are a strict, impartial evaluator of AI-generated explanations of social media posts.
Your job is to identify weaknesses, not to reward effort. Be critical and use the full 1–5 scale.
A score of 4 or 5 must be genuinely earned. Scores of 3 should be your default for adequate-but-unremarkable work.

You will receive:
- POST: the original social media post text
- EXPECTED EXPLANATION: a reference explanation describing the ideal answer
- RELEVANT CONTEXT: optional background context the agent should have surfaced
- EXPECTED SEARCH QUERIES: the ideal queries for researching this post
- GENERATED BULLETS: the agent's actual output bullets
- GENERATED SEARCH QUERIES: the queries the agent actually used
- SOURCES USED: URLs the agent cited

Rate on these seven dimensions:

1. explanation_relevance (1–5): Do the bullets cover the main ideas of the expected explanation without including irrelevant information?
   1 = bullets address something unrelated to the expected explanation
   2 = tangentially related but misses most of the core ideas
   3 = covers some key ideas but misses significant parts or adds off-topic content
   4 = covers most key ideas with only minor gaps or minor off-topic content
   5 = every key idea from the expected explanation is present, nothing irrelevant added

2. faithfulness (1–5): Are the bullet claims supported by the sources and post text, with no hallucinations?
   1 = contains clear factual errors or contradicts the sources/post
   2 = most claims are unverifiable or poorly supported
   3 = claims are plausible but sources provide only weak support
   4 = claims are clearly supported with only minor unsupported assertions
   5 = every claim is directly traceable to a source or the post text

3. groundedness (1–5): Does each bullet anchor in concrete evidence (post text, image, or source)?
   1 = bullets are entirely abstract or generic, no grounding
   2 = occasional concrete detail, mostly vague
   3 = some bullets are grounded, others float without evidence
   4 = most bullets cite or reference concrete evidence
   5 = every bullet is anchored in specific evidence from the post, image, or a source

4. completeness (1–5): Was any important information from the relevant context left out of the bullets?
   1 = critical context is entirely missing
   2 = major context gaps; the explanation is significantly incomplete
   3 = some important background is missing but the basics are there
   4 = nearly complete; only minor context details are absent
   5 = all key context from the relevant_context field is surfaced in the bullets

5. clarity (1–5): Are the bullets clear, concise, and free of unnecessary jargon?
   1 = confusing, jargon-heavy, or unreadable
   2 = understandable but awkward or overly technical for a general audience
   3 = readable but generic phrasing that could apply to any post on this topic
   4 = well-written and specific; a non-expert would understand immediately
   5 = exceptionally clear, precise, and engaging

6. context_relevance (1–5): Was the context retrieved actually necessary and useful for explaining the post?
   1 = retrieved context is irrelevant or contradicts the post
   2 = mostly irrelevant context was retrieved
   3 = some relevant context but also a lot of noise
   4 = most retrieved context is relevant with minor noise
   5 = all retrieved context directly supports understanding the post

7. search_query_relevance (1–5): Were the generated queries the right searches to understand the post?
   Use the expected_search_queries as a reference — do not require exact vocabulary match, judge intent.
   1 = queries would not find anything relevant to this post
   2 = queries are too broad or mostly off-target
   3 = queries are reasonable but miss the most important angles
   4 = queries cover the main angles with only minor gaps
   5 = queries are precise, well-targeted, and match the intent of the expected queries

Scoring rules:
- Do NOT give 5 unless genuinely exceptional. Do NOT give 4 just because there are no obvious errors.
- 3 is the appropriate default for work that is adequate but unremarkable.
- 1 or 2 is appropriate whenever the output fails its basic purpose in that dimension.
- Penalise vague filler bullets ("This post relates to an ongoing debate...") heavily on explanation_relevance and groundedness.
- If relevant_context is empty, score completeness as 3 (neutral) since there is no reference to check against.

Return ONLY valid JSON with this exact structure:
{
  "explanation_relevance": {"score": <1-5>, "reason": "<one sentence>"},
  "faithfulness": {"score": <1-5>, "reason": "<one sentence>"},
  "groundedness": {"score": <1-5>, "reason": "<one sentence>"},
  "completeness": {"score": <1-5>, "reason": "<one sentence>"},
  "clarity": {"score": <1-5>, "reason": "<one sentence>"},
  "context_relevance": {"score": <1-5>, "reason": "<one sentence>"},
  "search_query_relevance": {"score": <1-5>, "reason": "<one sentence>"}
}"""

_JUDGE_DIMENSIONS = (
    "explanation_relevance",
    "faithfulness",
    "groundedness",
    "completeness",
    "clarity",
    "context_relevance",
    "search_query_relevance",
)


def make_judge_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.openai_api_key, timeout=60.0)


async def llm_judge(
    post_text: str,
    bullets: list[dict],
    sources: list[str],
    expected_explanation: str = "",
    relevant_context: str = "",
    expected_search_queries: list[str] | None = None,
    generated_search_queries: list[str] | None = None,
    client: AsyncOpenAI | None = None,
) -> dict:
    """
    Returns a dict with one {score, reason} entry per dimension plus a
    normalized judge_score (mean of all dimension scores, 0–1).
    Pass a pre-built client to reuse the HTTP connection across multiple calls.
    """
    if client is None:
        client = make_judge_client()

    bullet_block = "\n".join(f"- {b.get('text', b) if isinstance(b, dict) else b}" for b in bullets)
    source_block = "\n".join(f"[Source {i+1}] {url}" for i, url in enumerate(sources))
    gen_queries_block = "\n".join(f"- {q}" for q in (generated_search_queries or []))
    exp_queries_block = "\n".join(f"- {q}" for q in (expected_search_queries or []))

    user_content = (
        f"POST:\n{post_text}\n\n"
        f"EXPECTED EXPLANATION:\n{expected_explanation}\n\n"
        f"RELEVANT CONTEXT:\n{relevant_context or '(none provided)'}\n\n"
        f"EXPECTED SEARCH QUERIES:\n{exp_queries_block or '(none provided)'}\n\n"
        f"GENERATED BULLETS:\n{bullet_block}\n\n"
        f"GENERATED SEARCH QUERIES:\n{gen_queries_block or '(none provided)'}\n\n"
        f"SOURCES USED:\n{source_block or '(none)'}"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _JUDGE_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
            temperature=0,
        )
        data = json.loads(response.choices[0].message.content or "{}")
    except Exception as exc:
        print(f"  [ERROR] llm_judge failed: {exc}")
        return {"error": str(exc), "judge_score": 0.0}

    scores = []
    for dim in _JUDGE_DIMENSIONS:
        entry = data.get(dim, {})
        if isinstance(entry, dict):
            s = entry.get("score")
        else:
            s = entry
        if isinstance(s, (int, float)):
            scores.append(s)

    judge_score = (sum(scores) / (5 * len(scores))) if scores else 0.0
    return {**data, "judge_score": round(judge_score, 3)}


async def llm_conclusion(aggregate: dict, case_results: list[dict], client: AsyncOpenAI | None = None) -> str:
    """
    Generates a short natural-language conclusion summarising the eval run.
    Returns a plain string. Falls back to empty string on error.
    """
    if client is None:
        client = make_judge_client()

    dim_scores_per_case = []
    for r in case_results:
        if r.get("skipped"):
            continue
        detail = r.get("judge_detail", {})
        per_dim = {}
        for dim in _JUDGE_DIMENSIONS:
            entry = detail.get(dim, {})
            per_dim[dim] = entry.get("score") if isinstance(entry, dict) else entry
        dim_scores_per_case.append({"id": r["id"], "judge_dims": per_dim})

    agg_block = "\n".join(f"  {k}: {v:.3f}" for k, v in aggregate.items())
    cases_block = json.dumps(dim_scores_per_case, indent=2)

    user_content = (
        f"AGGREGATE METRICS:\n{agg_block}\n\n"
        f"PER-CASE JUDGE DIMENSION SCORES:\n{cases_block}"
    )

    system = (
        "You are an AI evaluation analyst. You have just finished running an automated "
        "evaluation of an AI agent that explains Bluesky social media posts.\n\n"
        "Write a concise conclusion (4–6 sentences) that:\n"
        "1. States the overall performance level honestly.\n"
        "2. Identifies the 1–2 strongest dimensions.\n"
        "3. Identifies the 1–2 weakest dimensions and why they likely struggle.\n"
        "4. Gives one concrete, actionable suggestion for improvement.\n\n"
        "Be direct and specific. Do not pad with generic praise. Plain text only, no bullet points or headers."
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"  [ERROR] llm_conclusion failed: {exc}")
        return ""
