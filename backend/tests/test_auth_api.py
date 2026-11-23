from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


@pytest.fixture
def banco_simulado():
    """Substitui a sessão real por uma sessão simulada."""
    banco = MagicMock()

    def substituir_banco():
        yield banco

    app.dependency_overrides[get_db] = substituir_banco

    try:
        yield banco
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def cliente(banco_simulado):
    with TestClient(app) as test_client:
        yield test_client


def criar_usuario_ficticio(email="teste@example.com"):
    return SimpleNamespace(
        id=uuid4(),
        nome="Usuário Teste",
        email=email,
        senha_hash="hash-simulado",
    )


@pytest.mark.parametrize(
    "nome, email, senha",
    [
        ("Ana", "ana@example.com", "senha123"),
        ("Bruna", "bruna@example.com", "senhaSegura123"),
    ],
)
def test_cadastro_usuario_sucesso(
    cliente, banco_simulado, nome, email, senha, monkeypatch
):
    import app.routers.usuarios as usuarios_router

    banco_simulado.scalar.return_value = None

    monkeypatch.setattr(
        usuarios_router,
        "gerar_hash_senha",
        lambda senha: "hash-simulado",
    )

    # Simula a atribuição do ID após salvar no banco.
    def simular_refresh(usuario):
        usuario.id = uuid4()

    banco_simulado.refresh.side_effect = simular_refresh

    resposta = cliente.post(
        "/usuarios",
        json={
            "nome": nome,
            "email": email,
            "senha": senha,
            "aceita_termos": True,
            "aceita_privacidade": True,
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == nome
    assert resposta.json()["email"] == email
    assert "senha_hash" not in resposta.json()

    banco_simulado.add.assert_called_once()
    banco_simulado.commit.assert_called_once()


def test_cadastro_email_duplicado(cliente, banco_simulado):
    banco_simulado.scalar.return_value = criar_usuario_ficticio()

    resposta = cliente.post(
        "/usuarios",
        json={
            "nome": "Ana",
            "email": "teste@example.com",
            "senha": "senha123",
            "aceita_termos": True,
            "aceita_privacidade": True,
        },
    )

    assert resposta.status_code == 409
    banco_simulado.add.assert_not_called()


@pytest.mark.parametrize(
    "nome, email, senha",
    [
        ("A", "ana@example.com", "senha123"),
        ("Ana", "email-invalido", "senha123"),
        ("Ana", "ana@example.com", "1234567"),
    ],
)
def test_cadastro_dados_invalidos(
    cliente, nome, email, senha
):
    resposta = cliente.post(
        "/usuarios",
        json={
            "nome": nome,
            "email": email,
            "senha": senha,
        },
    )

    assert resposta.status_code == 422


def test_login_sucesso(cliente, banco_simulado, monkeypatch):
    import app.routers.auth as auth_router

    usuario = criar_usuario_ficticio()
    banco_simulado.scalar.return_value = usuario

    monkeypatch.setattr(
        auth_router,
        "verificar_senha",
        lambda senha, hash_senha: senha == "senha123",
    )

    resposta = cliente.post(
        "/auth/login",
        json={
            "email": usuario.email,
            "senha": "senha123",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["token_type"] == "bearer"
    assert isinstance(resposta.json()["access_token"], str)


@pytest.mark.parametrize(
    "senha_incorreta",
    ["senha-errada", "12345678", ""],
)
def test_login_senha_incorreta(
    cliente, banco_simulado, monkeypatch, senha_incorreta
):
    import app.routers.auth as auth_router

    banco_simulado.scalar.return_value = criar_usuario_ficticio()

    monkeypatch.setattr(
        auth_router,
        "verificar_senha",
        lambda senha, hash_senha: False,
    )

    resposta = cliente.post(
        "/auth/login",
        json={
            "email": "teste@example.com",
            "senha": senha_incorreta,
        },
    )

    assert resposta.status_code == 401


def test_login_usuario_inexistente(cliente, banco_simulado):
    banco_simulado.scalar.return_value = None

    resposta = cliente.post(
        "/auth/login",
        json={
            "email": "inexistente@example.com",
            "senha": "senha123",
        },
    )

    assert resposta.status_code == 401
