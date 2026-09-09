from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"

    __table_args__ = (
        Index(
            "uq_articles_source_external_id",
            "source_name",
            "external_id",
            unique=True,
            postgresql_where=text(
                "external_id IS NOT NULL"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    source_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    canonical_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    raw_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extracted_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cleaned_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    extraction_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    extraction_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
