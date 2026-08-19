"""WorkoutLog model — a client's logged result for a workout assignment.

`exercises` is kept as a simple JSON array of `{name, sets, reps, weight}`
objects for the MVP rather than a separate exercise table, per CLAUDE.md's
instruction to keep the implementation simple.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("workout_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercises: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
