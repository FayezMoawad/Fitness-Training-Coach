"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="Fitness Training Coach API")

app.include_router(health_router)
