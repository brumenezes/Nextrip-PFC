
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain_models import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from app.core.security import gerar_hash_senha

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED
)
def cadastrar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db)
):
    # Verifica se o e-mail já está cadastrado
    usuario_existente = db.scalar(
        select(Usuario).where(Usuario.email == dados.email)
    )

    if usuario_existente:
        raise HTTPException(
            status_code=409,
            detail="E-mail já cadastrado"
        )

    # Cria o usuário com a senha protegida
    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha)
    )

    db.add(novo_usuario)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="E-mail já cadastrado"
        )

    db.refresh(novo_usuario)

    return novo_usuario
