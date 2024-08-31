"""fix migration

Revision ID: 2c084e6c102a
Revises: 3a7802814195
Create Date: 2024-08-15 17:31:25.978543

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import fastapi_users_db_sqlalchemy

# revision identifiers, used by Alembic.
revision = "2c084e6c102a"
down_revision = "3a7802814195"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "instance",
        sa.Column("instance_id", sa.Integer(), nullable=False),
        sa.Column("instance_name", sa.Text(), nullable=False),
        sa.Column(
            "subscription_plan",
            sa.Enum(
                "ENTERPRISE",
                "PARTNER",
                name="instancesubscriptionplan",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            fastapi_users_db_sqlalchemy.generics.GUID(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("instance_id"),
    )
    op.create_table(
        "workspace",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("instance_id", sa.Integer(), nullable=True),
        sa.Column("Workspace_name", sa.Text(), nullable=False),
        sa.Column("custom_logo", sa.Text(), nullable=False),
        sa.Column("custom_header_logo", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["instance_id"],
            ["instance.instance_id"],
        ),
        sa.PrimaryKeyConstraint("workspace_id"),
    )
    op.create_table(
        "workspace__users",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column(
            "user_id",
            fastapi_users_db_sqlalchemy.generics.GUID(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.workspace_id"],
        ),
        sa.PrimaryKeyConstraint("workspace_id", "user_id"),
    )
    op.create_table(
        "workspace_settings",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("chat_page_enabled", sa.Boolean(), nullable=False),
        sa.Column("search_page_enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "default_page",
            sa.Enum("CHAT", "SEARCH", name="defaultpage", native_enum=False),
            nullable=False,
        ),
        sa.Column("maximum_chat_retention_days", sa.Integer(), nullable=False),
        sa.Column(
            "subscription_plan",
            sa.Enum(
                "BASIC",
                "PROFESSIONAL",
                "ORGANIZATION",
                name="workspacesubscriptionplan",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("number_of_users", sa.Integer(), nullable=False),
        sa.Column("storage_limit", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.workspace_id"],
        ),
        sa.PrimaryKeyConstraint("workspace_id"),
    )
    op.create_table(
        "workspace__teamspace",
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("teamspace_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["teamspace_id"],
            ["teamspace.id"],
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspace.workspace_id"],
        ),
        sa.PrimaryKeyConstraint("workspace_id", "teamspace_id"),
    )
    op.create_table(
        "celery_taskmeta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.String(length=155), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("result", sa.PickleType(), nullable=True),
        sa.Column("date_done", sa.DateTime(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("name", sa.String(length=155), nullable=True),
        sa.Column("args", sa.LargeBinary(), nullable=True),
        sa.Column("kwargs", sa.LargeBinary(), nullable=True),
        sa.Column("worker", sa.String(length=155), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=True),
        sa.Column("queue", sa.String(length=155), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
        sqlite_autoincrement=True,
    )
    op.create_table(
        "celery_tasksetmeta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("taskset_id", sa.String(length=155), nullable=True),
        sa.Column("result", sa.PickleType(), nullable=True),
        sa.Column("date_done", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("taskset_id"),
        sqlite_autoincrement=True,
    )
    op.drop_table("slack_bot_config")
    op.create_foreign_key(
        "api_key_owner_id_fk", "api_key", "user", ["owner_id"], ["id"]
    )
    op.create_foreign_key("api_key_user_id", "api_key", "user", ["user_id"], ["id"])
    op.alter_column(
        "chat_folder",
        "display_priority",
        existing_type=sa.INTEGER(),
        nullable=True,
    )
    # op.drop_constraint("chat_message_id_key", "chat_message", type_="unique")
    op.alter_column(
        "credential",
        "credential_json",
        existing_type=postgresql.BYTEA(),
        nullable=False,
    )
    op.drop_index(
        "ix_document_by_connector_credential_pair_pkey__connecto_27dc",
        table_name="document_by_connector_credential_pair",
    )
    op.add_column(
        "email_to_external_user_cache",
        sa.Column(
            "source_type",
            sa.Enum(
                "INGESTION_API",
                "WEB",
                "GOOGLE_DRIVE",
                "GMAIL",
                "GITHUB",
                "GITLAB",
                "CONFLUENCE",
                "JIRA",
                "PRODUCTBOARD",
                "FILE",
                "NOTION",
                "HUBSPOT",
                "GOOGLE_SITES",
                "ZENDESK",
                "DROPBOX",
                "SHAREPOINT",
                "TEAMS",
                "SALESFORCE",
                "S3",
                "R2",
                "GOOGLE_CLOUD_STORAGE",
                "OCI_STORAGE",
                name="documentsource",
                native_enum=False,
            ),
            nullable=False,
        ),
    )
    op.alter_column(
        "embedding_model", "status", existing_type=sa.VARCHAR(), nullable=False
    )
    op.create_index(
        "ix_embedding_model_future_unique",
        "embedding_model",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'FUTURE'"),
    )
    op.create_index(
        "ix_embedding_model_present_unique",
        "embedding_model",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'PRESENT'"),
    )
    op.alter_column(
        "llm_provider", "provider", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "saml",
        "expires_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "tool_call",
        "tool_result",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.add_column("teamspace", sa.Column("workspace_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "teamspace_workspace_id_fk",
        "teamspace",
        "workspace",
        ["workspace_id"],
        ["workspace_id"],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("teamspace_workspace_id_fk", "teamspace", type_="foreignkey")
    op.drop_column("teamspace", "workspace_id")
    op.alter_column(
        "tool_call",
        "tool_result",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.alter_column(
        "saml",
        "expires_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "llm_provider", "provider", existing_type=sa.VARCHAR(), nullable=True
    )
    op.drop_index(
        "ix_embedding_model_present_unique",
        table_name="embedding_model",
        postgresql_where=sa.text("status = 'PRESENT'"),
    )
    op.drop_index(
        "ix_embedding_model_future_unique",
        table_name="embedding_model",
        postgresql_where=sa.text("status = 'FUTURE'"),
    )
    op.alter_column(
        "embedding_model", "status", existing_type=sa.VARCHAR(), nullable=True
    )
    op.drop_column("email_to_external_user_cache", "source_type")
    op.create_index(
        "ix_document_by_connector_credential_pair_pkey__connecto_27dc",
        "document_by_connector_credential_pair",
        ["connector_id", "credential_id"],
        unique=False,
    )
    op.alter_column(
        "credential",
        "credential_json",
        existing_type=postgresql.BYTEA(),
        nullable=True,
    )
    op.create_unique_constraint("chat_message_id_key", "chat_message", ["id"])
    op.alter_column(
        "chat_folder",
        "display_priority",
        existing_type=sa.INTEGER(),
        nullable=False,
    )
    op.drop_constraint("api_key_owner_id_fk", "api_key", type_="foreignkey")
    op.drop_constraint("api_key_user_id_fk", "api_key", type_="foreignkey")
    op.create_table(
        "slack_bot_config",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("assistant_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "channel_config",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "response_type",
            sa.VARCHAR(length=9),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assistant_id"],
            ["assistant.id"],
            name="slack_bot_config_assistant_id_fkey",
        ),
        sa.PrimaryKeyConstraint("id", name="slack_bot_config_pkey"),
    )
    op.drop_table("celery_tasksetmeta")
    op.drop_table("celery_taskmeta")
    op.drop_table("workspace__teamspace")
    op.drop_table("workspace_settings")
    op.drop_table("workspace__users")
    op.drop_table("workspace")
    op.drop_table("instance")
    # ### end Alembic commands ###
