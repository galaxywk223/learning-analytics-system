"""add ai insights table

Revision ID: b83fdb2f9d60
Revises: f221f4a8359d
Create Date: 2025-11-03 22:50:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b83fdb2f9d60"
down_revision = "f221f4a8359d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_insight",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("insight_type", sa.String(length=20), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("scope_reference", sa.Integer(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("next_start_date", sa.Date(), nullable=True),
        sa.Column("next_end_date", sa.Date(), nullable=True),
        sa.Column("input_snapshot", sa.JSON(), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_ai_insight_user_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_insight_user_id"), "ai_insight", ["user_id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_ai_insight_user_id"), table_name="ai_insight")
    op.drop_table("ai_insight")
