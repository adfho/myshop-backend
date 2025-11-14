"""Add indexes for performance critical queries.

Revision ID: f7aa9dcd2d2b
Revises: 
Create Date: 2025-11-14 14:30:00.000000
"""

from alembic import op


revision = "f7aa9dcd2d2b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_order_user_id", "order", ["user_id"], unique=False)
    op.create_index("ix_order_created_at", "order", ["created_at"], unique=False)
    op.create_index(
        "ix_order_user_created_at",
        "order",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_notification_user_id", "notification", ["user_id"], unique=False)
    op.create_index(
        "ix_notification_user_read",
        "notification",
        ["user_id", "is_read"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_notification_user_read", table_name="notification")
    op.drop_index("ix_notification_user_id", table_name="notification")
    op.drop_index("ix_order_user_created_at", table_name="order")
    op.drop_index("ix_order_created_at", table_name="order")
    op.drop_index("ix_order_user_id", table_name="order")

