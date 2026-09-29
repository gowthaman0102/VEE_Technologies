from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    time_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="media", server_default="media")
    report_scope: Mapped[str] = mapped_column(String(50), nullable=False, default="standard", server_default="standard")
    business_impact_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    report_template: Mapped[str] = mapped_column(String(30), nullable=False, default="detailed", server_default="detailed")
    formats: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: ["pdf", "xlsx", "csv"])
    run_time_utc: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00", server_default="09:00")
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7, server_default="7")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)