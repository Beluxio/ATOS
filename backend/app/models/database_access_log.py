from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, UTC
from typing import Optional
from app.core.database import Base


class DatabaseAccessLog(Base):
    __tablename__ = "database_access_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_email: Mapped[str] = mapped_column(String(255), index=True)
    database_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(30))  # granted, revoked, expired, password_reset
    performed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
