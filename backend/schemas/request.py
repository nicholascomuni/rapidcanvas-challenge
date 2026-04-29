from pydantic import BaseModel, HttpUrl


class ExplainRequest(BaseModel):
    url: HttpUrl
