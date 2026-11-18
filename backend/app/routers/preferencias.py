
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain_models import Usuario, Preferencias
from app.schemas.preferencias import (
    PreferenciasCreate,
    PreferenciasResponse
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Preferências"]
)


@router.post(
    "/{usuario_id}/preferencias",
    response_model=PreferenciasResponse,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_preferencias(
    usuario_id: UUID,
    dados: PreferenciasCreate,
    db: Session = Depends(get_db)
):
    # Verifica se o usuário existe
    usuario = db.get(Usuario, usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )

    # Verifica se já existem preferências cadastradas
    preferencias_existentes = db.scalar(
        select(Preferencias).where(
            Preferencias.usuario_id == usuario_id
        )
    )

    if preferencias_existentes:
        raise HTTPException(
            status_code=409,
            detail="Preferências já cadastradas para este usuário"
        )

    # Cria as preferências
    novas_preferencias = Preferencias(
        usuario_id=usuario_id,
        orcamento_maximo=dados.orcamento_maximo
    )

    db.add(novas_preferencias)
    db.commit()
    db.refresh(novas_preferencias)

    return novas_preferencias


@router.get(
    "/{usuario_id}/preferencias",
    response_model=PreferenciasResponse
)
def consultar_preferencias(
    usuario_id: UUID,
    db: Session = Depends(get_db)
):
    # Busca as preferências do usuário
    preferencias = db.scalar(
        select(Preferencias).where(
            Preferencias.usuario_id == usuario_id
        )
    )

    if preferencias is None:
        raise HTTPException(
            status_code=404,
            detail="Preferências não encontradas"
        )

    return preferencias


@router.put(
    "/{usuario_id}/preferencias",
    response_model=PreferenciasResponse
)
def atualizar_preferencias(
    usuario_id: UUID,
    dados: PreferenciasCreate,
    db: Session = Depends(get_db)
):
    # Busca as preferências existentes
    preferencias = db.scalar(
        select(Preferencias).where(
            Preferencias.usuario_id == usuario_id
        )
    )

    if preferencias is None:
        raise HTTPException(
            status_code=404,
            detail="Preferências não encontradas"
        )

    # Atualiza o orçamento
    preferencias.orcamento_maximo = dados.orcamento_maximo

    db.commit()
    db.refresh(preferencias)

    return preferencias

