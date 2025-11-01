"""Reset primary key sequences for PostgreSQL to fix sync issues after data import.

Revision ID: fd9a1b2c3e4f
Revises: ce12d6fcae15
Create Date: 2025-07-10 10:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd9a1b2c3e4f'
down_revision = 'ce12d6fcae15'
branch_labels = None
depends_on = None

# A list of all tables that have auto-incrementing integer primary keys.
TABLES_WITH_SEQUENCES = [
    'user', 'stage', 'weekly_data', 'daily_data', 'log_entry',
    'countdown_event', 'motto', 'todo', 'category', 'sub_category',
    'milestone_category', 'milestone', 'milestone_attachment', 'daily_plan_item'
]

def upgrade():
    """
    Resets the primary key sequence for all specified tables if the database
    is PostgreSQL. This is crucial after a manual data import to prevent
    "duplicate key" errors.
    """
    # Get the current connection's dialect name
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        print("PostgreSQL detected. Resetting primary key sequences...")
        for table_name in TABLES_WITH_SEQUENCES:
            try:
                # The sequence name is typically table_name + '_id_seq'
                sequence_name = f"{table_name}_id_seq"

                # --- FIX: Add double quotes around the table name ---
                # This prevents conflicts with SQL reserved keywords like "user".
                sql_command = f"""
                    SELECT setval(
                        '{sequence_name}',
                        COALESCE((SELECT MAX(id) FROM "{table_name}"), 1),
                        (SELECT MAX(id) FROM "{table_name}") IS NOT NULL
                    );
                """
                op.execute(sql_command)
                print(f"  - Sequence '{sequence_name}' for table '{table_name}' has been reset.")
            except Exception as e:
                # Catch exceptions on a per-table basis so that one failure
                # doesn't abort the entire migration transaction.
                print(f"  - WARNING: Could not reset sequence for table '{table_name}'. Error: {e}")
    else:
        # If not using PostgreSQL (e.g., local SQLite), skip this operation.
        print(f"Skipping sequence reset for non-PostgreSQL dialect: {conn.dialect.name}")


def downgrade():
    """
    Downgrading this operation is not typically necessary, as it only corrects
    the state of the sequence. We'll leave it empty.
    """
    pass
