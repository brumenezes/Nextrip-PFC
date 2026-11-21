from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.routers.usuarios import alterar_senha
from app.schemas.usuario import AlterarSenhaRequest


def criar_contexto():
    banco = MagicMock()
    usuario = SimpleNamespace(
        id=uuid4(),
        nome="Usuário Teste",
        email="teste@example.com",
        senha_hash="hash-antigo",
    )
    return banco, usuario


def test_alterar_senha_com_sucesso(monkeypatch):
    import app.routers.usuarios as usuarios_router

    banco, usuario = criar_contexto()
    monkeypatch.setattr(
        usuarios_router,
        "verificar_senha",
        lambda senha, _hash: senha == "senha-atual",
    )
    monkeypatch.setattr(usuarios_router, "gerar_hash_senha", lambda _senha: "hash-novo")

    resposta = alterar_senha(
        AlterarSenhaRequest(senha_atual="senha-atual", nova_senha="senha-nova-123"),
        banco,
        usuario,
    )

    assert resposta.status_code == 204
    assert usuario.senha_hash == "hash-novo"
    banco.commit.assert_called_once()


def test_alterar_senha_rejeita_senha_atual_incorreta(monkeypatch):
    import app.routers.usuarios as usuarios_router

    banco, usuario = criar_contexto()
    monkeypatch.setattr(usuarios_router, "verificar_senha", lambda _senha, _hash: False)

    with pytest.raises(HTTPException) as erro:
        alterar_senha(
            AlterarSenhaRequest(senha_atual="incorreta", nova_senha="senha-nova-123"),
            banco,
            usuario,
        )

    assert erro.value.status_code == 400
    assert erro.value.detail == "Senha atual incorreta"
    banco.commit.assert_not_called()


def test_alterar_senha_valida_tamanho_da_nova_senha():
    with pytest.raises(ValidationError):
        AlterarSenhaRequest(senha_atual="senha-atual", nova_senha="curta")
