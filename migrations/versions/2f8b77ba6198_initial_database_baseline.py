
"""Initial database baseline

Revision ID: 2f8b77ba6198
Revises:
"""

from alembic import op
from app.models import db

revision = "2f8b77ba6198"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    db.metadata.create_all(bind=op.get_bind())


def downgrade():
    db.metadata.drop_all(bind=op.get_bind())
