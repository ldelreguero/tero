"""rename-oath-token-table

Revision ID: cd7c53fb4cf7
Revises: 5e943851d1d6
Create Date: 2026-01-07 15:54:50.273400

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cd7c53fb4cf7'
down_revision: Union[str, None] = '5e943851d1d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE tooloauthtokentype RENAME TO toolauthtokentype")
    op.rename_table('tool_oauth_token', 'tool_auth_token')
    op.execute("ALTER INDEX ix_tool_oauth_token_updated_at RENAME TO ix_tool_auth_token_updated_at")


def downgrade() -> None:
    op.execute("ALTER INDEX ix_tool_auth_token_updated_at RENAME TO ix_tool_oauth_token_updated_at")
    op.rename_table('tool_auth_token', 'tool_oauth_token')
    op.execute("ALTER TYPE toolauthtokentype RENAME TO tooloauthtokentype")
