"""add ai chat tables

Revision ID: c3f7d4a9b112
Revises: b83fdb2f9d60
Create Date: 2026-03-13 12:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c3f7d4a9b112"
down_revision = "b83fdb2f9d60"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_chat_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_reference", sa.Integer(), nullable=True),
        sa.Column("date_reference", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "last_message_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_ai_chat_session_user_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_chat_session_user_id"),
        "ai_chat_session",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "ai_chat_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_reference", sa.Integer(), nullable=True),
        sa.Column("date_reference", sa.Date(), nullable=True),
        sa.Column("generation_mode", sa.String(length=30), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("meta_snapshot", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["ai_chat_session.id"],
            name="fk_ai_chat_message_session_id",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_ai_chat_message_user_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_chat_message_session_id"),
        "ai_chat_message",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_chat_message_user_id"),
        "ai_chat_message",
        ["user_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_ai_chat_message_user_id"), table_name="ai_chat_message")
    op.drop_index(op.f("ix_ai_chat_message_session_id"), table_name="ai_chat_message")
    op.drop_table("ai_chat_message")
    op.drop_index(op.f("ix_ai_chat_session_user_id"), table_name="ai_chat_session")
    op.drop_table("ai_chat_session")
