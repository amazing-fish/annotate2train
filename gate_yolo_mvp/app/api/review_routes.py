from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/queue")
def review_queue() -> list[dict]:
    return []
