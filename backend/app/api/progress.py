"""Coach progress-review route — thin, delegates to progress_service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.schemas.progress import ClientProgressResponse
from app.services import progress_service

router = APIRouter(tags=["progress"])


@router.get("/clients/{client_id}/progress", response_model=ClientProgressResponse)
def get_client_progress(
    client_id: int,
    coach: User = Depends(require_role(UserRole.coach)),
    db: Session = Depends(get_db),
):
    try:
        return progress_service.get_client_progress(db, coach, client_id)
    except progress_service.NoClientRelationshipError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        ) from None
