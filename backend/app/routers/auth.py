
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain_models import Usuario
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verificar_senha
from app.core.auth import criar_token_acesso

router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)


@router.post("/login", response_model=TokenResponse)
def login(
    dados: LoginRequest,
    db: Session = Depends(get_db)
):
    # Procura o usuário pelo e-mail
    usuario = db.scalar(
        select(Usuario).where(Usuario.email == dados.email)
    )

    # Verifica se o usuário existe e se a senha está correta
    if usuario is None or not verificar_senha(
        dados.senha, usuario.senha_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Gera o token JWT
    token = criar_token_acesso(str(usuario.id))

    return TokenResponse(access_token=token)
