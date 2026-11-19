from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core.auth import (
    criar_token_acesso,
    SECRET_KEY,
    ALGORITHM,
)


@pytest.fixture
def ambiente_jwt():
    banco = MagicMock()

    usuario = SimpleNamespace(
        id=uuid4(),
        nome="Usuário Teste",
        email="teste@example.com",
    )

    def substituir_banco():
        yield banco

    app.dependency_overrides[get_db] = substituir_banco

    try:
        with TestClient(app) as cliente:
            yield cliente, banco, usuario
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_acesso_sem_token(ambiente_jwt):
    cliente, banco, usuario = ambiente_jwt

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias"
    )

    assert resposta.status_code == 401
    banco.get.assert_not_called()


@pytest.mark.parametrize(
    "token",
    [
        "token-invalido",
        "abc.def.ghi",
        "",
    ],
)
def test_acesso_token_invalido(ambiente_jwt, token):
    cliente, banco, usuario = ambiente_jwt

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_acesso_token_expirado(ambiente_jwt):
    cliente, banco, usuario = ambiente_jwt

    token = jwt.encode(
        {
            "sub": str(usuario.id),
            "exp": datetime.now(timezone.utc)
            - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_acesso_token_com_id_invalido(ambiente_jwt):
    cliente, banco, usuario = ambiente_jwt

    token = criar_token_acesso("id-nao-e-uuid")

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_acesso_token_usuario_inexistente(ambiente_jwt):
    cliente, banco, usuario = ambiente_jwt

    banco.get.return_value = None
    token = criar_token_acesso(str(usuario.id))

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 401


def test_acesso_token_valido(ambiente_jwt):
    cliente, banco, usuario = ambiente_jwt

    banco.get.return_value = usuario
    banco.scalar.return_value = SimpleNamespace(
        id=uuid4(),
        usuario_id=usuario.id,
        orcamento_maximo=100,
        interesses=["Museu"],
    )

    token = criar_token_acesso(str(usuario.id))

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["usuario_id"] == str(usuario.id)


def test_token_valido_sem_permissao(ambiente_jwt):
    cliente, banco, usuario = ambiente_jwt

    banco.get.return_value = usuario
    outro_usuario_id = uuid4()

    token = criar_token_acesso(str(usuario.id))

    resposta = cliente.get(
        f"/usuarios/{outro_usuario_id}/preferencias",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resposta.status_code == 403
