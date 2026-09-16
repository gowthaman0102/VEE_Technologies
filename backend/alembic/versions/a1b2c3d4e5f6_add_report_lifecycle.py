"""add report lifecycle and duplicate prevention

Revision ID: a1b2c3d4e5f6
Revises: 9f1a2c3d4e5f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9f1a2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generated_reports",
        sa.Column("status", sa.String(length=20), server_default="success", nullable=False),
    )
    op.add_column("generated_reports", sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("generated_reports", sa.Column("error", sa.String(length=1000), nullable=True))
    op.create_index("ix_generated_reports_status", "generated_reports", ["status"])
    op.create_unique_constraint(
        "uq_generated_report_period_format",
        "generated_reports",
        ["company_id", "report_type", "period_start", "period_end", "file_format"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_generated_report_period_format", "generated_reports", type_="unique")
    op.drop_index("ix_generated_reports_status", table_name="generated_reports")
    op.drop_column("generated_reports", "error")
    op.drop_column("generated_reports", "generated_at")
    op.drop_column("generated_reports", "status")
