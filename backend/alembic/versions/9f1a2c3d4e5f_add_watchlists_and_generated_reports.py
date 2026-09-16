"""add watchlists and generated reports

Revision ID: 9f1a2c3d4e5f
Revises: 47c5d55524ec
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f1a2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "47c5d55524ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_watchlist_items_company_id", "watchlist_items", ["company_id"])
    op.create_index("ix_watchlist_items_item_type", "watchlist_items", ["item_type"])
    op.create_index("ix_watchlist_items_item_name", "watchlist_items", ["item_name"])

    op.create_table(
        "generated_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("file_format", sa.String(length=20), nullable=False),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_reports_company_id", "generated_reports", ["company_id"])
    op.create_index("ix_generated_reports_created_at", "generated_reports", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_generated_reports_created_at", table_name="generated_reports")
    op.drop_index("ix_generated_reports_company_id", table_name="generated_reports")
    op.drop_table("generated_reports")
    op.drop_index("ix_watchlist_items_item_name", table_name="watchlist_items")
    op.drop_index("ix_watchlist_items_item_type", table_name="watchlist_items")
    op.drop_index("ix_watchlist_items_company_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
