"""add database-backed company configurations

Revision ID: 7a1c5f2e9d10
Revises: 4cf419fa38c4
Create Date: 2026-09-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7a1c5f2e9d10"
down_revision = "4cf419fa38c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_configurations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column("risk", sa.JSON(), nullable=True),
        sa.Column("alerts", sa.JSON(), nullable=True),
        sa.Column("reports", sa.JSON(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("branding", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )
    op.create_index(
        "ix_company_configurations_company_id",
        "company_configurations",
        ["company_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_company_configurations_company_id",
        table_name="company_configurations",
    )
    op.drop_table("company_configurations")
