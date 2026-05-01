from pydantic import BaseModel


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
