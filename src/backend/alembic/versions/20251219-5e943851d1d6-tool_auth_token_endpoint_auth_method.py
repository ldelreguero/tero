"""tool_auth_token_endpoint_auth_method

Revision ID: 5e943851d1d6
Revises: 4f3f4b5477dd
Create Date: 2025-12-19 14:06:50.589964

"""
import sqlalchemy as sa
import sqlmodel
from typing import Sequence, Union
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5e943851d1d6'
down_revision: Union[str, None] = '4f3f4b5477dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tool_oauth_client_info', sa.Column('token_endpoint_auth_method', sqlmodel.AutoString(), nullable=True))
    op.execute("UPDATE tool_oauth_client_info SET token_endpoint_auth_method = 'client_secret_post' WHERE client_id <> ''")
    op.execute("UPDATE tool_oauth_client_info SET token_endpoint_auth_method = 'none' WHERE client_id = ''")


def downgrade() -> None:
    op.drop_column('tool_oauth_client_info', 'token_endpoint_auth_method')
