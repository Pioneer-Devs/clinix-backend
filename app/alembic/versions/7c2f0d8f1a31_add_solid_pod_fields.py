"""add solid pod fields

Revision ID: 7c2f0d8f1a31
Revises: fbce173913d8
Create Date: 2026-07-03 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "7c2f0d8f1a31"
down_revision: Union[str, None] = "fbce173913d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("solid_pod_url", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column("patients", sa.Column("solid_web_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column("patients", sa.Column("solid_token_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column("patients", sa.Column("solid_token_secret", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))

    with op.batch_alter_table("wallet_records") as batch_op:
        batch_op.add_column(sa.Column("solid_pod_url", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
        batch_op.drop_column("encrypted_summary")
        batch_op.drop_column("encryption_iv")


def downgrade() -> None:
    with op.batch_alter_table("wallet_records") as batch_op:
        batch_op.add_column(sa.Column("encryption_iv", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False))
        batch_op.add_column(sa.Column("encrypted_summary", sqlmodel.sql.sqltypes.AutoString(), nullable=False))
        batch_op.drop_column("solid_pod_url")

    op.drop_column("patients", "solid_token_secret")
    op.drop_column("patients", "solid_token_id")
    op.drop_column("patients", "solid_web_id")
    op.drop_column("patients", "solid_pod_url")
