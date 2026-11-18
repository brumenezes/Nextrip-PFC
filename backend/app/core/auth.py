
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv

# Localiza o .env na raiz do projeto Nextrip-PFC
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_PATH)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY não configurada no arquivo .env"
    )


def criar_token_acesso(usuario_id: str) -> str:
    """Gera um token JWT para o usuário autenticado."""

    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=EXPIRE_MINUTES
    )

    payload = {
        "sub": usuario_id,
        "exp": expiracao
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def validar_token(token: str) -> str | None:
    """Valida o token e retorna o ID do usuário."""

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload.get("sub")

    except jwt.InvalidTokenError:
        return None
