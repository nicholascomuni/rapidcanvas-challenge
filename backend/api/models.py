from pydantic import BaseModel, HttpUrl


AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4.1",
    "gpt-4.1-mini",
    "o3-mini",
]

DEFAULT_MODEL = "gpt-4o"


class ExplainRequest(BaseModel):
    url: HttpUrl
    model: str = DEFAULT_MODEL


class BulletPoint(BaseModel):
    text: str


class PostMeta(BaseModel):
    author_handle: str
    text: str
    image_url: str | None


class ExplainResponse(BaseModel):
    post: PostMeta
    bullets: list[BulletPoint]
    sources: list[str]
    search_queries: list[str] = []
