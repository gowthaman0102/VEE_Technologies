"""add report schedules, recipients, and template identity

Revision ID: d3a9b6f42c10
Revises: 8b2d6e3fa411
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3a9b6f42c10"
down_revision: Union[str, Sequence[str], None] = "8b2d6e3fa411"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_schedules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("report_type", sa.String(length=20), nullable=False),
        sa.Column("time_mode", sa.String(length=20), server_default="media", nullable=False),
        sa.Column("report_scope", sa.String(length=50), server_default="standard", nullable=False),
        sa.Column("business_impact_category", sa.String(length=50), nullable=True),
        sa.Column("report_template", sa.String(length=30), server_default="detailed", nullable=False),
        sa.Column("formats", sa.JSON(), nullable=False),
        sa.Column("run_time_utc", sa.String(length=5), server_default="09:00", nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("custom_period_days", sa.Integer(), server_default="7", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_report_schedules_company_id", "report_schedules", ["company_id"])
    op.create_index("ix_report_schedules_next_run_at", "report_schedules", ["next_run_at"])

    op.create_table(
        "report_recipients",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("company_id", "email", name="uq_report_recipient_company_email"),
    )
    op.create_index("ix_report_recipients_company_id", "report_recipients", ["company_id"])

    op.add_column("generated_reports", sa.Column("report_template", sa.String(length=30), server_default="detailed", nullable=False))
    op.add_column("generated_reports", sa.Column("schedule_id", sa.Integer(), nullable=True))
    op.create_index("ix_generated_reports_schedule_id", "generated_reports", ["schedule_id"])

def downgrade() -> None:
    op.drop_index("ix_generated_reports_schedule_id", table_name="generated_reports")
    op.drop_column("generated_reports", "schedule_id")
    op.drop_column("generated_reports", "report_template")
    op.drop_index("ix_report_recipients_company_id", table_name="report_recipients")
    op.drop_table("report_recipients")
    op.drop_index("ix_report_schedules_next_run_at", table_name="report_schedules")
    op.drop_index("ix_report_schedules_company_id", table_name="report_schedules")
    op.drop_table("report_schedules")