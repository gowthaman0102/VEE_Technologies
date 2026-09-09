"""change article embedding dimensions to 384

Revision ID: e26fd6852e6b
Revises: ab25b05d0652
Create Date: 2026-09-09 23:02:26.027501
"""

from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e26fd6852e6b"
down_revision: Union[str, Sequence[str], None] = "ab25b05d0652"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _reset_embedding_data() -> None:
    """Clear generated embeddings before changing vector dimensions."""

    op.execute(
        sa.text(
            """
            UPDATE articles
            SET
                embedding = NULL,
                embedding_model = NULL,
                embedding_status = 'pending',
                embedding_error = NULL,
                embedded_at = NULL
            """
        )
    )


def upgrade() -> None:
    """Change article embeddings from 1536 to 384 dimensions."""

    op.drop_index(
        "ix_articles_embedding_hnsw_cosine",
        table_name="articles",
    )

    _reset_embedding_data()

    op.alter_column(
        "articles",
        "embedding",
        existing_type=Vector(1536),
        type_=Vector(384),
        existing_nullable=True,
        postgresql_using="embedding::vector(384)",
    )

    op.create_index(
        "ix_articles_embedding_hnsw_cosine",
        "articles",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={
            "embedding": "vector_cosine_ops",
        },
        postgresql_where=sa.text(
            "embedding IS NOT NULL"
        ),
    )


def downgrade() -> None:
    """Restore article embeddings to 1536 dimensions."""

    op.drop_index(
        "ix_articles_embedding_hnsw_cosine",
        table_name="articles",
    )

    _reset_embedding_data()

    op.alter_column(
        "articles",
        "embedding",
        existing_type=Vector(384),
        type_=Vector(1536),
        existing_nullable=True,
        postgresql_using="embedding::vector(1536)",
    )

    op.create_index(
        "ix_articles_embedding_hnsw_cosine",
        "articles",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={
            "embedding": "vector_cosine_ops",
        },
        postgresql_where=sa.text(
            "embedding IS NOT NULL"
        ),
    )
