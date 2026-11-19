from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


@pytest.fixture
def ambiente_poi():
    banco = MagicMock()

    def substituir_banco():
        yield banco

    app.dependency_overrides[get_db] = substituir_banco

    try:
        with TestClient(app) as cliente:
            yield cliente, banco
    finally:
        app.dependency_overrides.pop(get_db, None)


def dados_poi_validos():
    return {
        "nome": "Museu do Ipiranga",
        "categoria": "Museu",
        "latitude": -23.5855,
        "longitude": -46.6097,
        "preco_estimado": 30,
        "duracao_minutos": 120,
        "avaliacao_media": 4.7,
    }


def criar_poi_ficticio():
    return SimpleNamespace(
        id=uuid4(),
        nome="Museu do Ipiranga",
        categoria="Museu",
        preco_estimado=30,
        duracao_minutos=120,
        avaliacao_media=4.7,
        osm_id=None,
        google_place_id=None,
    )


# ==========================================
# CADASTRO DE PONTOS TURÍSTICOS
# ==========================================

def test_cadastrar_poi_sucesso(ambiente_poi):
    cliente, banco = ambiente_poi

    banco.scalar.return_value = None

    def simular_refresh(poi):
        poi.id = uuid4()

    banco.refresh.side_effect = simular_refresh
    banco.execute.return_value.one.return_value = (
        -23.5855,
        -46.6097,
    )

    resposta = cliente.post(
        "/pontos-interesse",
        json=dados_poi_validos(),
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Museu do Ipiranga"
    assert resposta.json()["latitude"] == -23.5855
    assert resposta.json()["longitude"] == -46.6097

    banco.add.assert_called_once()
    banco.commit.assert_called_once()


def test_cadastrar_poi_duplicado(ambiente_poi):
    cliente, banco = ambiente_poi

    banco.scalar.return_value = criar_poi_ficticio()

    resposta = cliente.post(
        "/pontos-interesse",
        json=dados_poi_validos(),
    )

    assert resposta.status_code == 409
    banco.add.assert_not_called()
    banco.commit.assert_not_called()


# ==========================================
# CONSULTA DE PONTOS TURÍSTICOS
# ==========================================

def test_listar_pontos_interesse(ambiente_poi):
    cliente, banco = ambiente_poi

    poi = criar_poi_ficticio()

    banco.execute.return_value.all.return_value = [
        (poi, -23.5855, -46.6097),
    ]

    resposta = cliente.get("/pontos-interesse")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["nome"] == "Museu do Ipiranga"


def test_listar_pontos_interesse_vazio(ambiente_poi):
    cliente, banco = ambiente_poi

    banco.execute.return_value.all.return_value = []

    resposta = cliente.get("/pontos-interesse")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_consultar_poi_por_id(ambiente_poi):
    cliente, banco = ambiente_poi

    poi = criar_poi_ficticio()

    banco.execute.return_value.one_or_none.return_value = (
        poi,
        -23.5855,
        -46.6097,
    )

    resposta = cliente.get(
        f"/pontos-interesse/{poi.id}"
    )

    assert resposta.status_code == 200
    assert resposta.json()["id"] == str(poi.id)


def test_consultar_poi_inexistente(ambiente_poi):
    cliente, banco = ambiente_poi

    banco.execute.return_value.one_or_none.return_value = None

    resposta = cliente.get(
        f"/pontos-interesse/{uuid4()}"
    )

    assert resposta.status_code == 404


# ==========================================
# VALIDAÇÃO DOS DADOS
# ==========================================

@pytest.mark.parametrize(
    "campo, valor_invalido",
    [
        ("latitude", -91),
        ("latitude", 91),
        ("longitude", -181),
        ("longitude", 181),
        ("preco_estimado", -1),
        ("duracao_minutos", 0),
        ("duracao_minutos", -10),
        ("avaliacao_media", -0.1),
        ("avaliacao_media", 5.1),
        ("nome", ""),
    ],
)
def test_rejeitar_dados_invalidos(
    ambiente_poi, campo, valor_invalido
):
    cliente, banco = ambiente_poi

    dados = dados_poi_validos()
    dados[campo] = valor_invalido

    resposta = cliente.post(
        "/pontos-interesse",
        json=dados,
    )

    assert resposta.status_code == 422
    banco.add.assert_not_called()
    banco.commit.assert_not_called()
