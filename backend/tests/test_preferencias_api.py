from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core.dependencies import obter_usuario_atual


@pytest.fixture
def ambiente_teste():
    banco = MagicMock()

    usuario = SimpleNamespace(
        id=uuid4(),
        nome="Usuário Teste",
        email="teste@example.com",
    )

    def substituir_banco():
        yield banco

    app.dependency_overrides[get_db] = substituir_banco
    app.dependency_overrides[obter_usuario_atual] = lambda: usuario

    try:
        with TestClient(app) as cliente:
            yield cliente, banco, usuario
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(obter_usuario_atual, None)


def criar_preferencias(usuario_id, orcamento=100, interesses=None):
    return SimpleNamespace(
        id=uuid4(),
        usuario_id=usuario_id,
        orcamento_maximo=orcamento,
        interesses=interesses if interesses is not None else ["Museu"],
    )


def test_cadastrar_preferencias_sucesso(ambiente_teste):
    cliente, banco, usuario = ambiente_teste

    banco.get.return_value = usuario
    banco.scalar.return_value = None

    def simular_refresh(preferencias):
        preferencias.id = uuid4()

    banco.refresh.side_effect = simular_refresh

    resposta = cliente.post(
        f"/usuarios/{usuario.id}/preferencias",
        json={
            "orcamento_maximo": 150,
            "interesses": ["Museu", "Parque"],
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["orcamento_maximo"] == 150
    assert resposta.json()["interesses"] == ["Museu", "Parque"]

    banco.add.assert_called_once()
    banco.commit.assert_called_once()


def test_preferencias_duplicadas(ambiente_teste):
    cliente, banco, usuario = ambiente_teste

    banco.get.return_value = usuario
    banco.scalar.return_value = criar_preferencias(usuario.id)

    resposta = cliente.post(
        f"/usuarios/{usuario.id}/preferencias",
        json={
            "orcamento_maximo": 100,
            "interesses": ["Museu"],
        },
    )

    assert resposta.status_code == 409


def test_consultar_preferencias_sucesso(ambiente_teste):
    cliente, banco, usuario = ambiente_teste

    banco.scalar.return_value = criar_preferencias(usuario.id)

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias"
    )

    assert resposta.status_code == 200
    assert resposta.json()["usuario_id"] == str(usuario.id)


def test_consultar_preferencias_inexistentes(ambiente_teste):
    cliente, banco, usuario = ambiente_teste

    banco.scalar.return_value = None

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/preferencias"
    )

    assert resposta.status_code == 404


def test_atualizar_preferencias_sucesso(ambiente_teste):
    cliente, banco, usuario = ambiente_teste

    preferencias = criar_preferencias(usuario.id)
    banco.scalar.return_value = preferencias

    resposta = cliente.put(
        f"/usuarios/{usuario.id}/preferencias",
        json={
            "orcamento_maximo": 200,
            "interesses": ["Gastronomia"],
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["orcamento_maximo"] == 200
    assert resposta.json()["interesses"] == ["Gastronomia"]

    banco.commit.assert_called_once()


@pytest.mark.parametrize(
    "metodo",
    ["get", "post", "put"],
)
def test_usuario_nao_pode_acessar_preferencias_de_outro(
    ambiente_teste, metodo
):
    cliente, banco, usuario = ambiente_teste
    outro_usuario_id = uuid4()

    dados = {
        "orcamento_maximo": 100,
        "interesses": ["Museu"],
    }

    resposta = getattr(cliente, metodo)(
        f"/usuarios/{outro_usuario_id}/preferencias",
        **({"json": dados} if metodo != "get" else {}),
    )

    assert resposta.status_code == 403
    banco.commit.assert_not_called()


@pytest.mark.parametrize(
    "orcamento",
    [-1, -0.01, -100],
)
def test_rejeitar_orcamento_negativo(
    ambiente_teste, orcamento
):
    cliente, banco, usuario = ambiente_teste

    resposta = cliente.post(
        f"/usuarios/{usuario.id}/preferencias",
        json={
            "orcamento_maximo": orcamento,
            "interesses": ["Museu"],
        },
    )

    assert resposta.status_code == 422
    banco.commit.assert_not_called()
