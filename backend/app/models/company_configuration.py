from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompanyConfiguration(Base):
    __tablename__ = "company_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    sources: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    risk: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    alerts: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    reports: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    features: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    branding: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
