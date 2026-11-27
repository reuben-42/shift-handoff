"""FastAPI app factory.

Run with: uvicorn handoff.infrastructure.main:create_app --factory
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from handoff.adapters.api.routers import health
from handoff.infrastructure.config import Settings
from handoff.infrastructure.container import Container


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="Shift Handoff Copilot API",
        version="0.1.0",
        description="Synthetic data. Demo only. Not for clinical use.",
    )
    app.state.container = Container.build(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    return app
