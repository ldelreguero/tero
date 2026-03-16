"""remove_icon_bg

Revision ID: c3ae0aefa4d1
Revises: cd7c53fb4cf7
Create Date: 2025-12-30 11:03:23.402115

"""
from io import BytesIO
from typing import Sequence, Union

from PIL import Image
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3ae0aefa4d1'
down_revision: Union[str, None] = 'cd7c53fb4cf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, icon, icon_bg_color FROM agent WHERE icon IS NOT NULL")).fetchall()

    for agent_id, icon_bytes, bg_color in rows:
        if not icon_bytes or not bg_color:
            continue

        new_icon = _create_icon_with_background(icon_bytes=icon_bytes, bg_color=bg_color)
        if new_icon != icon_bytes:
            conn.execute(sa.text("UPDATE agent SET icon = :icon WHERE id = :id"), {"icon": new_icon, "id": agent_id})

    op.drop_column('agent', 'icon_bg_color')


def downgrade() -> None:
    # Background colors were baked into the PNG bytes during upgrade,
    # so the original `icon_bg_color` values cannot be restored.
    op.add_column('agent', sa.Column('icon_bg_color', sa.VARCHAR(length=6), autoincrement=False, nullable=True))


def _create_icon_with_background(icon_bytes: bytes, bg_color: str) -> bytes:
    try:
        icon_img = Image.open(BytesIO(icon_bytes))
        if icon_img.mode != 'RGBA':
            icon_img = icon_img.convert('RGBA')
        try:
            bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
            bg_image = Image.new('RGBA', icon_img.size, bg_rgb + (255,))
            result_img = Image.alpha_composite(bg_image, icon_img)
        except (ValueError, TypeError):
            result_img = icon_img
        output = BytesIO()
        result_img.save(output, format='PNG')
        return output.getvalue()
    except Exception:
        return icon_bytes
