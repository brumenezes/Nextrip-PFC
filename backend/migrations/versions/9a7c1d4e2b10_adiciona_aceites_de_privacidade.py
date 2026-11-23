"""Adiciona aceites versionados de termos e privacidade

Revision ID: 9a7c1d4e2b10
Revises: cef8e48e846f
"""

from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a7c1d4e2b10"
down_revision: Union[str, Sequence[str], None] = "cef8e48e846f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    instante_migracao = datetime.now(timezone.utc)
    op.add_column("usuario", sa.Column("termos_versao", sa.String(length=20), nullable=True))
    op.add_column("usuario", sa.Column("termos_aceitos_em", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuario", sa.Column("privacidade_versao", sa.String(length=20), nullable=True))
    op.add_column("usuario", sa.Column("privacidade_aceita_em", sa.DateTime(timezone=True), nullable=True))
    op.execute(
        sa.text(
            "UPDATE usuario SET termos_versao=:versao, termos_aceitos_em=:instante, "
            "privacidade_versao=:versao, privacidade_aceita_em=:instante"
        ).bindparams(versao="legado-2026-11-22", instante=instante_migracao)
    )
    op.alter_column("usuario", "termos_versao", nullable=False)
    op.alter_column("usuario", "termos_aceitos_em", nullable=False)
    op.alter_column("usuario", "privacidade_versao", nullable=False)
    op.alter_column("usuario", "privacidade_aceita_em", nullable=False)


def downgrade() -> None:
    op.drop_column("usuario", "privacidade_aceita_em")
    op.drop_column("usuario", "privacidade_versao")
    op.drop_column("usuario", "termos_aceitos_em")
    op.drop_column("usuario", "termos_versao")
