import asyncio
import json
import re

import httpx
from openai import AsyncOpenAI
from tavily import TavilyClient

from core.config import get_settings

from .state import AgentState

_BSKY_BASE = "https://public.api.bsky.app/xrpc"
_URL_PATTERN = re.compile(
    r"https?://bsky\.app/profile/(?P<handle>[^/]+)/post/(?P<rkey>[A-Za-z0-9]+"
    r")"
)


# ---------------------------------------------------------------------------
# fetch_post_node
# ---------------------------------------------------------------------------

def _extract_image(post: dict) -> str | None:
    embed = post.get("embed") or {}
    embed_type = embed.get("$type", "")
    if embed_type == "app.bsky.embed.images#view":
        images = embed.get("images", [])
        if images:
            return images[0].get("thumb")
    if embed_type == "app.bsky.embed.external#view":
        return embed.get("external", {}).get("thumb")
    return None


async def fetch_post_node(state: AgentState) -> AgentState:
    url = state["post_url"]
    m = _URL_PATTERN.match(url)
    if not m:
        return {**state, "error": f"Invalid Bluesky URL: {url}"}

    handle = m.group("handle")
    rkey = m.group("rkey")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resolve = await client.get(
                f"{_BSKY_BASE}/com.atproto.identity.resolveHandle",
                params={"handle": handle},
            )
            resolve.raise_for_status()
            did = resolve.json().get("did")
            if not did:
                return {**state, "error": "Could not resolve Bluesky handle."}

            at_uri = f"at://{did}/app.bsky.feed.post/{rkey}"
            thread = await client.get(
                f"{_BSKY_BASE}/app.bsky.feed.getPostThread",
                params={"uri": at_uri, "depth": 0},
            )
            thread.raise_for_status()
            thread_data = thread.json()

    except Exception as exc:
        return {**state, "error": f"Bluesky fetch failed: {exc}"}

    post = thread_data.get("thread", {}).get("post")
    if not post:
        return {**state, "error": "Could not parse post data from Bluesky response."}

    record = post.get("record", {})
    author = post.get("author", {})

    return {
        **state,
        "post_text": record.get("text", ""),
        "author": author.get("handle", handle),
        "image_url": _extract_image(post),
        "error": None,
    }


# ---------------------------------------------------------------------------
# vision_node
# ---------------------------------------------------------------------------

async def vision_node(state: AgentState) -> AgentState:
    image_url = state.get("image_url")
    if not image_url:
        return state

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = (
        "Analyze this image and return your response in this exact format:\n"
        "DESCRIPTION: [2-3 sentence visual description of what the image shows]\n"
        "EXTRACTED_TEXT: [all text visible in the image verbatim, or NONE if no text]"
    )

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}},
                    ],
                }
            ],
            max_tokens=300,
            temperature=0,
        )
        raw = response.choices[0].message.content or ""
    except Exception as exc:
        return {**state, "image_description": None, "image_extracted_text": None}

    description: str | None = None
    extracted_text: str | None = None

    for line in raw.splitlines():
        if line.startswith("DESCRIPTION:"):
            description = line[len("DESCRIPTION:"):].strip()
        elif line.startswith("EXTRACTED_TEXT:"):
            val = line[len("EXTRACTED_TEXT:"):].strip()
            extracted_text = None if val.upper() == "NONE" else val

    return {**state, "image_description": description, "image_extracted_text": extracted_text}


# ---------------------------------------------------------------------------
# analyze_node
# ---------------------------------------------------------------------------

async def analyze_node(state: AgentState) -> AgentState:
    parts = [state.get("post_text", "")]
    if state.get("image_description"):
        parts.append(f"Image description: {state['image_description']}")
    if state.get("image_extracted_text"):
        parts.append(f"Text in image: {state['image_extracted_text']}")
    combined = "\n".join(parts)

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant. Given a social media post, generate 2-3 precise "
                        "search queries that would find relevant background context, origin stories, "
                        "key people involved, and broader significance. Return ONLY a JSON array of "
                        "query strings, nothing else."
                    ),
                },
                {"role": "user", "content": combined},
            ],
            response_format={"type": "json_object"},
            max_tokens=200,
            temperature=0,
        )
        raw = response.choices[0].message.content or "[]"
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            queries = parsed
        else:
            queries = next(iter(parsed.values()), [])
        queries = [str(q) for q in queries[:3] if q]
    except Exception:
        queries = [state.get("post_text", "")[:200]]

    return {**state, "search_queries": queries}


# ---------------------------------------------------------------------------
# search_node
# ---------------------------------------------------------------------------

async def search_node(state: AgentState) -> AgentState:
    queries = state.get("search_queries", [])
    if not queries:
        return {**state, "search_results": [], "sources": []}

    settings = get_settings()
    tavily = TavilyClient(api_key=settings.tavily_api_key)

    async def _search_one(query: str) -> list[dict]:
        try:
            data = await asyncio.to_thread(
                tavily.search,
                query=query,
                search_depth="advanced",
                include_raw_content=True,
                max_results=5,
            )
            results = []
            for r in data.get("results", []):
                content = r.get("raw_content") or r.get("content") or ""
                results.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "content": content[:1500],
                })
            return results
        except Exception:
            return []

    all_batches = await asyncio.gather(*[_search_one(q) for q in queries])

    seen: set[str] = set()
    deduped: list[dict] = []
    for batch in all_batches:
        for r in batch:
            if r["url"] and r["url"] not in seen:
                seen.add(r["url"])
                deduped.append(r)

    sources = [r["url"] for r in deduped]
    return {**state, "search_results": deduped, "sources": sources}


# ---------------------------------------------------------------------------
# synthesize_node
# ---------------------------------------------------------------------------

async def synthesize_node(state: AgentState) -> AgentState:
    post_text = state.get("post_text", "")
    results = state.get("search_results", [])

    context_blocks = []
    for i, r in enumerate(results, start=1):
        context_blocks.append(f"[Source {i}] {r['title']}\nURL: {r['url']}\n{r['content']}")
    context = "\n\n".join(context_blocks)

    user_parts = [f"POST TEXT:\n{post_text}"]
    if state.get("image_description"):
        user_parts.append(f"IMAGE DESCRIPTION:\n{state['image_description']}")
    if state.get("image_extracted_text"):
        user_parts.append(f"TEXT IN IMAGE:\n{state['image_extracted_text']}")
    if context:
        user_parts.append(f"SEARCH CONTEXT:\n{context}")
    user_message = "\n\n".join(user_parts)

    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at explaining social media posts. Given a post and research "
                        "results, write exactly 3-5 bullet points that explain the context, background, "
                        "key people or concepts involved, and why this post is significant or funny. "
                        "Each bullet should be 1-2 sentences. Be specific and informative, not vague. "
                        'Return ONLY a JSON object: {"bullets": [...], "sources": [...]}'
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.3,
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        bullets = [str(b) for b in parsed.get("bullets", []) if b]
        sources = [str(s) for s in parsed.get("sources", state.get("sources", []))]
    except Exception as exc:
        return {**state, "error": f"Synthesis failed: {exc}"}

    return {**state, "bullets": bullets, "sources": sources}
