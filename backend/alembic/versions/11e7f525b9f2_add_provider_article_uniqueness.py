"""add provider article uniqueness

Revision ID: 11e7f525b9f2
Revises: 529066e2c59e
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op


revision: str = "11e7f525b9f2"
down_revision: Union[str, Sequence[str], None] = "529066e2c59e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_articles_source_external_id",
        "articles",
        [
            "source_name",
            "external_id",
        ],
        unique=True,
        postgresql_where=(
            "external_id IS NOT NULL"
        ),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_articles_source_external_id",
        table_name="articles",
    )
