"""add publisher country to article

Revision ID: 4cf419fa38c4
Revises: 3bf419fa38c3
Create Date: 2026-09-24 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cf419fa38c4'
down_revision = '3bf419fa38c3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('articles', sa.Column('publisher_country_code', sa.String(length=2), nullable=True))
    op.add_column('articles', sa.Column('publisher_country_name', sa.String(length=100), nullable=True))
    op.add_column('articles', sa.Column('publisher_country_method', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_articles_publisher_country_code'), 'articles', ['publisher_country_code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_articles_publisher_country_code'), table_name='articles')
    op.drop_column('articles', 'publisher_country_method')
    op.drop_column('articles', 'publisher_country_name')
    op.drop_column('articles', 'publisher_country_code')
