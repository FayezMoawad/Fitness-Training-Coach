"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.logs import router as logs_router
from app.api.progress import router as progress_router
from app.api.workouts import router as workouts_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Fitness Training Coach API")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workouts_router)
app.include_router(logs_router)
app.include_router(progress_router)


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for anything not already turned into an HTTPException
    (e.g. a DB failure). Per CLAUDE.md, internal error detail must never
    reach the client — full detail is logged server-side only."""
    logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
