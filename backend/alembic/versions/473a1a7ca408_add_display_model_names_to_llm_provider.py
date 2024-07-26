"""Add display_model_names to llm_provider

Revision ID: 473a1a7ca408
Revises: 91ffac7e65b3
Create Date: 2024-07-25 14:31:02.002917

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "473a1a7ca408"
down_revision = "91ffac7e65b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "llm_provider",
        sa.Column("display_model_names", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("llm_provider", "display_model_names")
