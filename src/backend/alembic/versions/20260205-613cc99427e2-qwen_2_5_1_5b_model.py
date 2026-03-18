"""qwen_2.5_1.5b_model

Revision ID: 613cc99427e2
Revises: c3ae0aefa4d1
Create Date: 2026-02-05 16:23:32.147821

"""
from typing import Sequence, Union
from alembic import op
from alembic_postgresql_enum import TableReference

# revision identifiers, used by Alembic.
revision: str = '613cc99427e2'
down_revision: Union[str, None] = 'c3ae0aefa4d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.sync_enum_values( # type: ignore
        enum_schema='public',
        enum_name='llmmodelvendor',
        new_values=['ANTHROPIC', 'GOOGLE', 'OPENAI', 'QWEN'],
        affected_columns=[TableReference(table_schema='public', table_name='llm_model', column_name='model_vendor')],
        enum_values_to_rename=[],
    )
    op.execute("""
        INSERT INTO llm_model (id, name, description, token_limit, output_token_limit, prompt_1k_token_usd, completion_1k_token_usd, model_type, model_vendor) VALUES
        ('qwen-2.5-1.5b', 'Qwen 2.5 1.5B', 'This is a free, open‑source model for simple tasks and basic coding; less capable than GPT‑4o Mini and GPT‑4.1 Nano.', 128000, 8000, 0.0, 0.0, 'CHAT', 'QWEN')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM llm_model WHERE id = 'qwen-2.5-1.5b'")
    op.sync_enum_values( # type: ignore
        enum_schema='public',
        enum_name='llmmodelvendor',
        new_values=['ANTHROPIC', 'GOOGLE', 'OPENAI'],
        affected_columns=[TableReference(table_schema='public', table_name='llm_model', column_name='model_vendor')],
        enum_values_to_rename=[],
    )
