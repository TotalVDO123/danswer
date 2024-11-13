"""add_multiple_slack_bot_support

Revision ID: 4ee1287bd26a
Revises: 9cf5c00f72fe
Create Date: 2024-11-06 13:15:53.302644

"""
import logging
from typing import cast
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from danswer.key_value_store.factory import get_kv_store
from danswer.db.models import EncryptedString, SlackApp

# revision identifiers, used by Alembic.
revision = "4ee1287bd26a"
down_revision = "9cf5c00f72fe"
branch_labels: None = None
depends_on: None = None

# Configure logging
logger = logging.getLogger("alembic.runtime.migration")
logger.setLevel(logging.INFO)


def upgrade() -> None:
    logger.info(f"{revision}: create_table: slack_app")
    op.create_table(
        "slack_app",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("bot_token", EncryptedString, nullable=False),
        sa.Column("app_token", EncryptedString, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bot_token", name="uq_bot_token"),
        sa.UniqueConstraint("app_token", name="uq_app_token"),
    )

    logger.info(f"{revision}: add_column: slack_bot_config.app_id")
    op.add_column(
        "slack_bot_config",
        sa.Column("app_id", sa.Integer(), nullable=True),
    )

    try:
        logger.info(f"{revision}: Checking for existing Slack bot.")

        tokens = cast(dict, get_kv_store().load("slack_bot_tokens_config_key"))

        bot_token = tokens.get("bot_token")
        if not bot_token:
            logger.info("bot_token not found")
            raise ValueError("bot_token not found")

        app_token = tokens.get("app_token")
        if not app_token:
            logger.info("app_token not found")
            raise ValueError("app_token not found")

        logger.info(f"{revision}: Found bot and app tokens.")
    except ValueError as vex:
        # Ignore if the dynamic config is not found
        logger.debug(f"{revision}: Exception: {vex}")
        logger.info(f"{revision}: This is OK if there was not an existing Slack bot.")

    logger.info(f"{revision}: Migrating slack app settings.")

    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        new_slack_app = SlackApp(
            name="Slack App (Migrated)",
            description="Migrated app",
            enabled=True,
            bot_token=bot_token,
            app_token=app_token,
        )
        session.add(new_slack_app)
        session.commit()

        first_row_id = new_slack_app.id
        # Update all rows in the slack_bot_config to set the foreign key app_id to first_row_id
        if not first_row_id:
            raise RuntimeError(
                f"{revision}: Migrated slack bot, but could not find a row in slack_app!"
            )

        logger.info(f"{revision}: Migrating slack bot configs.")
        op.execute(
            sa.text("UPDATE slack_bot_config SET app_id = :first_row_id").bindparams(
                first_row_id=first_row_id
            )
        )
    except Exception as e:
        session.rollback()
        logger.exception(f"{revision}: Exception during migration: {e}")
        raise
    finally:
        session.close()

    # Delete the tokens in dynamic config
    if bot_token and app_token:
        logger.info(f"{revision}: Removing old bot and app tokens.")
        get_kv_store().delete("slack_bot_tokens_config_key")

    logger.info(f"{revision}: Applying foreign key constraint to Slack bot configs.")
    sa.ForeignKeyConstraint(
        ["app_id"],
        ["slack_app.id"],
    ),

    logger.info(f"{revision}: Migration complete.")


def downgrade() -> None:
    op.drop_column("slack_bot_config", "app_id")
    op.drop_table("slack_app")
