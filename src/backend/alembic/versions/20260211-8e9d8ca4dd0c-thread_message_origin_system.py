"""thread_message_origin_system

Revision ID: 8e9d8ca4dd0c
Revises: fd24763a078c
Create Date: 2026-02-11 19:05:25.867844

"""
import sqlalchemy as sa
import sqlmodel
from typing import Sequence, Union
from alembic import op
from alembic_postgresql_enum import TableReference

# revision identifiers, used by Alembic.
revision: str = '8e9d8ca4dd0c'
down_revision: Union[str, None] = 'fd24763a078c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.sync_enum_values( # type: ignore
        enum_schema="public",
        enum_name="threadmessageorigin",
        new_values=["USER", "AGENT", "SYSTEM"],
        affected_columns=[TableReference(table_schema="public", table_name="thread_message", column_name="origin")],
        enum_values_to_rename=[],
    )


def downgrade() -> None:
    op.sync_enum_values( # type: ignore
        enum_schema="public",
        enum_name="threadmessageorigin",
        new_values=["USER", "AGENT"],
        affected_columns=[TableReference(table_schema="public", table_name="thread_message", column_name="origin")],
        enum_values_to_rename=[],
    )
