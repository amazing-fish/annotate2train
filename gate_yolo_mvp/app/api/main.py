from __future__ import annotations

from fastapi import FastAPI

from app.api.review_routes import router as review_router
from app.api.run_routes import router as run_router


def create_app() -> FastAPI:
    app = FastAPI(title="gate-bag-pipeline")
    app.include_router(review_router)
    app.include_router(run_router)
    return app
