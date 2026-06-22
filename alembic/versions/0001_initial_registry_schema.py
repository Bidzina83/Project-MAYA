"""initial registry schema

Revision ID: 0001_initial_registry_schema
Revises: 
Create Date: 2026-06-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_registry_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # embeddings table
    op.create_table(
        'embeddings',
        sa.Column('chunk_id', sa.Text(), primary_key=True),
        sa.Column('embedding_path', sa.Text(), nullable=True),
        sa.Column('source_path', sa.Text(), nullable=True),
        sa.Column('source_hash', sa.Text(), nullable=True),
        sa.Column('model', sa.Text(), nullable=True),
        sa.Column('extractor_version', sa.Text(), nullable=True),
        sa.Column('embedding_timestamp', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.Text(), nullable=True),
    )

    # entries table
    op.create_table(
        'entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('embedding_id', sa.Text(), nullable=True, unique=True),
        sa.Column('chunk_id', sa.Text(), nullable=True),
        sa.Column('vector', sa.Text(), nullable=True),
        sa.Column('vector_dim', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.Text(), nullable=True),
        sa.Column('source_path', sa.Text(), nullable=True),
        sa.Column('score_meta', sa.Text(), nullable=True),
        sa.Column('normalized_vector', sa.Text(), nullable=True),
        sa.Column('normalized_vector_dim', sa.Integer(), nullable=True),
        sa.Column('normalized_vector_algo', sa.Text(), nullable=True),
        sa.Column('normalized_at', sa.Text(), nullable=True),
        sa.Column('normalized_version', sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_table('entries')
    op.drop_table('embeddings')
