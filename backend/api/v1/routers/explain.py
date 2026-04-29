from fastapi import APIRouter, HTTPException

from agent.graph import graph
from schemas.request import ExplainRequest
from schemas.response import BulletPoint, ExplainResponse, PostMeta

router = APIRouter(tags=["explain"])


@router.post("/explain", response_model=ExplainResponse)
async def explain_post(request: ExplainRequest) -> ExplainResponse:
    initial_state = {
        "post_url": str(request.url),
        "post_text": "",
        "author": "",
        "image_url": None,
        "image_description": None,
        "image_extracted_text": None,
        "search_queries": [],
        "search_results": [],
        "bullets": [],
        "sources": [],
        "iteration_count": 0,
        "error": None,
    }

    final_state = await graph.ainvoke(initial_state)

    if final_state.get("error"):
        raise HTTPException(status_code=502, detail=final_state["error"])

    if not final_state.get("bullets"):
        raise HTTPException(status_code=502, detail="Agent produced no bullet points.")

    return ExplainResponse(
        post=PostMeta(
            author_handle=final_state["author"],
            text=final_state["post_text"],
            image_url=final_state.get("image_url"),
        ),
        bullets=[BulletPoint(text=b) for b in final_state["bullets"]],
        sources=final_state.get("sources", []),
    )
