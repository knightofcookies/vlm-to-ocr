"""Initial migration

Revision ID: 75c5171dd81b
Revises:
Create Date: 2026-02-10 16:49:03.927932

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "75c5171dd81b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # manifest table
    op.create_table(
        "manifest",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("doc_type", sa.String(), nullable=True),
        sa.Column("download_date", sa.DateTime(), nullable=True),
        sa.Column("sarvam_lang_code", sa.Text(), nullable=True),
        sa.Column("query_language", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("identifier"),
    )

    # documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("manifest_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["manifest_id"],
            ["manifest.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ocr_batches table
    op.create_table(
        "ocr_batches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("sarvam_job_id", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("failed_pages", sa.Text(), nullable=True),
        sa.Column("output_dir", sa.Text(), nullable=True),
        sa.Column("zip_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sarvam_job_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ocr_batches")
    op.drop_table("documents")
    op.drop_table("manifest")
