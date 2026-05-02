"""
Post fetchers for different social networks.

To add a new network: implement PostFetcher and register it in FETCHERS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass
class PostData:
    text: str
    author: str
    image_url: str | None


class PostFetcher(Protocol):
    def can_handle(self, url: str) -> bool: ...
    async def fetch(self, url: str) -> PostData: ...


# ---------------------------------------------------------------------------
# Bluesky
# ---------------------------------------------------------------------------

_BSKY_BASE = "https://public.api.bsky.app/xrpc"
_BSKY_PATTERN = re.compile(r"https?://bsky\.app/profile/(?P<handle>[^/]+)/post/(?P<rkey>[A-Za-z0-9]+)")


class BlueSkyFetcher:
    def can_handle(self, url: str) -> bool:
        return bool(_BSKY_PATTERN.match(url))

    async def fetch(self, url: str) -> PostData:
        m = _BSKY_PATTERN.match(url)
        if not m:
            raise ValueError(f"Invalid Bluesky URL: {url}")

        handle, rkey = m.group("handle"), m.group("rkey")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resolve = await client.get(
                f"{_BSKY_BASE}/com.atproto.identity.resolveHandle",
                params={"handle": handle},
            )
            if resolve.status_code == 400:
                raise ValueError(f"User '@{handle}' not found on Bluesky.")
            resolve.raise_for_status()
            did = resolve.json().get("did")
            if not did:
                raise ValueError("Could not resolve Bluesky handle.")

            thread = await client.get(
                f"{_BSKY_BASE}/app.bsky.feed.getPostThread",
                params={"uri": f"at://{did}/app.bsky.feed.post/{rkey}", "depth": 0},
            )
            if thread.status_code == 404:
                raise ValueError("Post not found. It may have been deleted or the URL is incorrect.")
            thread.raise_for_status()

        thread_obj = thread.json().get("thread", {})
        post = thread_obj.get("post", {})
        record = post.get("record", {})
        author = post.get("author", {})

        return PostData(
            text=record.get("text", ""),
            author=author.get("handle", handle),
            image_url=_extract_image(post),
        )


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


# Registry — add new fetchers here
FETCHERS: list[PostFetcher] = [
    BlueSkyFetcher(),
]


def get_fetcher(url: str) -> PostFetcher:
    for fetcher in FETCHERS:
        if fetcher.can_handle(url):
            return fetcher
    raise ValueError(f"No fetcher available for URL: {url}")
