"""Repair application tables missing from a database stamped at the current head.

Revision ID: 7a91c4d2e6f0
Revises: 4e1e2e530b71

This is intentionally additive: create_all(checkfirst=True) creates only
missing tables and does not drop or rewrite existing tables or records.
"""
from alembic import op
from app.models import db

revision = "7a91c4d2e6f0"
down_revision = "4e1e2e530b71"
branch_labels = None
depends_on = None


def upgrade():
    db.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade():
    # Deliberately non-destructive. This repair must not drop application data.
    pass
