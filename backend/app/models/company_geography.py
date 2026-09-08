from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompanyGeography(Base):
    __tablename__ = "company_geographies"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "geography",
            name="uq_company_geographies_company_geography",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    geography: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
