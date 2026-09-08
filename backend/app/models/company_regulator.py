from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CompanyRegulator(Base):
    __tablename__ = "company_regulators"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "regulator",
            name="uq_company_regulators_company_regulator",
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

    regulator: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )
