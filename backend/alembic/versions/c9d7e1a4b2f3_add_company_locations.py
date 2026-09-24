"""add verified company locations

Revision ID: c9d7e1a4b2f3
Revises: 8ab5ac365549
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d7e1a4b2f3"
down_revision: Union[str, Sequence[str], None] = "8ab5ac365549"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("location_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("source", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_locations_company_id", "company_locations", ["company_id"])
    op.execute(
        sa.text(
            """
            INSERT INTO company_locations
                (company_id, location_type, name, city, region, country,
                 latitude, longitude, verified, source)
            SELECT id, 'headquarters', 'OpenAI headquarters', 'San Francisco',
                   'California', 'United States', 37.7749, -122.4194, true,
                   'Verified company profile configuration'
            FROM companies
            WHERE lower(name) = 'openai'
            AND NOT EXISTS (
                SELECT 1 FROM company_locations existing
                WHERE existing.company_id = companies.id
                AND existing.location_type = 'headquarters'
            )
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_company_locations_company_id", table_name="company_locations")
    op.drop_table("company_locations")
