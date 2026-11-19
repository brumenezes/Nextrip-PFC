from uuid import uuid4

import jwt
import pytest

from app.core.auth import (
    criar_token_acesso,
    validar_token,
    SECRET_KEY,
    ALGORITHM,
)
from app.core.security import (
    gerar_hash_senha,
    verificar_senha,
)


# ==========================================
# TESTES DE SENHAS
# ==========================================

@pytest.mark.parametrize(
    "senha",
    [
        "senha123",
        "SenhaSegura@2026",
        "12345678",
    ],
)
def test_gerar_e_verificar_senha(senha):
    senha_hash = gerar_hash_senha(senha)

    assert senha_hash != senha
    assert verificar_senha(senha, senha_hash) is True


@pytest.mark.parametrize(
    "senha_correta, senha_incorreta",
    [
        ("senha123", "senha456"),
        ("SenhaSegura@2026", "senha123"),
        ("12345678", "87654321"),
    ],
)
def test_rejeitar_senha_incorreta(
    senha_correta,
    senha_incorreta,
):
    senha_hash = gerar_hash_senha(senha_correta)

    assert verificar_senha(
        senha_incorreta,
        senha_hash,
    ) is False


# ==========================================
# TESTES DE JWT
# ==========================================

def test_criar_e_validar_token():
    usuario_id = str(uuid4())

    token = criar_token_acesso(usuario_id)

    assert isinstance(token, str)
    assert validar_token(token) == usuario_id


@pytest.mark.parametrize(
    "token_invalido",
    [
        "token-invalido",
        "",
        "abc.def.ghi",
    ],
)
def test_rejeitar_token_invalido(token_invalido):
    assert validar_token(token_invalido) is None


def test_rejeitar_token_expirado():
    from datetime import datetime, timedelta, timezone

    payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(timezone.utc)
        - timedelta(minutes=1),
    }

    token_expirado = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    assert validar_token(token_expirado) is None


def test_rejeitar_token_assinado_com_chave_errada():
    payload = {"sub": str(uuid4())}

    token = jwt.encode(
        payload,
        "chave-incorreta-exclusiva-para-teste",
        algorithm=ALGORITHM,
    )

    assert validar_token(token) is None
