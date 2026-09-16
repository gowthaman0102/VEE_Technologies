from datetime import datetime

from sqlalchemy import (
    DateTime,
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


class ArticleBusinessImpact(Base):
    __tablename__ = "article_business_impacts"

    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "company_id",
            name="uq_article_business_impacts_article_company",
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

    primary_category: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    categories: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    impact_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    model: Mapped[str] = mapped_column(
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
