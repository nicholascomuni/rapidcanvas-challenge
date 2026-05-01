from typing import TypedDict


class AgentState(TypedDict):
    post_url: str
    post_text: str
    author: str
    image_url: str | None
    image_description: str | None
    image_extracted_text: str | None
    search_queries: list[str]
    search_results: list[dict]
    bullets: list[str]
    sources: list[str]
    iteration_count: int
    model: str
    error: str | None
