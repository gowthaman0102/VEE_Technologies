"""persist deterministic publisher-country resolution

Revision ID: d4e8f6a1b2c3
Revises: c9d7e1a4b2f3
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8f6a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c9d7e1a4b2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("publisher_country_code", sa.String(2), nullable=True))
    op.add_column("articles", sa.Column("publisher_country", sa.String(120), nullable=True))
    op.add_column("articles", sa.Column("publisher_country_resolution", sa.String(60), nullable=True))
    op.create_index("ix_articles_publisher_country_code", "articles", ["publisher_country_code"])
    op.create_index("ix_articles_publisher_country", "articles", ["publisher_country"])


def downgrade() -> None:
    op.drop_index("ix_articles_publisher_country", table_name="articles")
    op.drop_index("ix_articles_publisher_country_code", table_name="articles")
    op.drop_column("articles", "publisher_country_resolution")
    op.drop_column("articles", "publisher_country")
    op.drop_column("articles", "publisher_country_code")
