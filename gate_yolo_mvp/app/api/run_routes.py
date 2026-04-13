from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/health")
def run_health() -> dict[str, bool]:
    return {"ok": True}
