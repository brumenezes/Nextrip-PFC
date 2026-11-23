from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain_models import Usuario
from app.schemas.usuario import AlterarSenhaRequest, UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.core.privacy import PRIVACY_NOTICE_VERSION, TERMS_VERSION
from app.core.dependencies import obter_usuario_atual
from app.core.security import gerar_hash_senha, verificar_senha

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
        senha_hash=gerar_hash_senha(dados.senha),
        termos_versao=TERMS_VERSION,
        termos_aceitos_em=datetime.now(timezone.utc),
        privacidade_versao=PRIVACY_NOTICE_VERSION,
        privacidade_aceita_em=datetime.now(timezone.utc),
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


@router.get("/me", response_model=UsuarioResponse)
def consultar_usuario_atual(
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    return usuario_atual


@router.patch("/me", response_model=UsuarioResponse)
def atualizar_usuario_atual(
    dados: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    email_em_uso = db.scalar(
        select(Usuario).where(
            Usuario.email == dados.email,
            Usuario.id != usuario_atual.id,
        )
    )
    if email_em_uso:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    usuario_atual.nome = dados.nome
    usuario_atual.email = str(dados.email)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    db.refresh(usuario_atual)
    return usuario_atual


@router.put(
    "/me/senha",
    status_code=status.HTTP_204_NO_CONTENT,
)
def alterar_senha(
    dados: AlterarSenhaRequest,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(obter_usuario_atual),
):
    if not verificar_senha(dados.senha_atual, usuario_atual.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )

    if verificar_senha(dados.nova_senha, usuario_atual.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ser diferente da senha atual",
        )

    usuario_atual.senha_hash = gerar_hash_senha(dados.nova_senha)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
