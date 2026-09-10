from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ArticleTriage(Base):
    __tablename__ = "article_triages"

    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "company_id",
            name="uq_article_triages_article_company",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    article_id: Mapped[int] = mapped_column(
        ForeignKey(
            "articles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    why_it_matters: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    potential_impact: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    urgency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    llm_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
