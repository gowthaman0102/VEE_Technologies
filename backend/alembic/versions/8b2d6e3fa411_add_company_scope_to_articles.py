"""add company scope to articles

Revision ID: 8b2d6e3fa411
Revises: 7a1c5f2e9d10
Create Date: 2026-09-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "8b2d6e3fa411"
down_revision = "7a1c5f2e9d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("company_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_articles_company_id_companies",
        "articles",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_articles_company_id", "articles", ["company_id"], unique=False)
    op.execute(
        """
        UPDATE articles
        SET company_id = (
            SELECT id FROM companies
            WHERE is_active = TRUE
            ORDER BY id
            LIMIT 1
        )
        WHERE company_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_articles_company_id", table_name="articles")
    op.drop_constraint("fk_articles_company_id_companies", "articles", type_="foreignkey")
    op.drop_column("articles", "company_id")
