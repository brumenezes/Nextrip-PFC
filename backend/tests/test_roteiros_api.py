from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core.dependencies import obter_usuario_atual


@pytest.fixture
def ambiente_roteiros():
    banco = MagicMock()

    usuario = SimpleNamespace(
        id=uuid4(),
        nome="Usuario Teste",
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


def dados_roteiro_validos():
    return {
        "data_visita": "2026-11-24",
        "tempo_disponivel_minutos": 360,
        "orcamento_maximo": 150,
    }


def criar_ponto(nome, categoria, preco, duracao, avaliacao):
    return SimpleNamespace(
        id=uuid4(),
        nome=nome,
        categoria=categoria,
        preco_estimado=preco,
        duracao_minutos=duracao,
        avaliacao_media=avaliacao,
    )


def preparar_geracao(banco):
    museu = criar_ponto("Museu", "Museu", 30, 120, 4.9)
    parque = criar_ponto("Parque", "Parque", 0, 120, 4.8)

    banco.scalar.return_value = SimpleNamespace(
        interesses=["Museu"],
    )

    banco.scalars.return_value.all.return_value = [
        museu,
        parque,
    ]

    banco.execute.return_value.all.return_value = [
        SimpleNamespace(
            id=museu.id,
            latitude=-23.5855,
            longitude=-46.6097,
        ),
        SimpleNamespace(
            id=parque.id,
            latitude=-23.5874,
            longitude=-46.6576,
        ),
    ]

    def simular_refresh(objeto):
        objeto.id = uuid4()

    banco.refresh.side_effect = simular_refresh

    return museu, parque


# ==========================================
# GERACAO DE ROTEIROS
# ==========================================

def test_gerar_roteiro_sucesso(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados_roteiro_validos(),
    )

    assert resposta.status_code == 201

    resultado = resposta.json()

    assert resultado["custo_total_estimado"] <= 150
    assert resultado["tempo_total_roteiro"] <= 360
    assert len(resultado["atividades"]) == 2
    assert resultado["atividades"][0]["nome"] == "Museu"

    assert resultado["tempo_total_deslocamentos"] > 0

    assert resultado["tempo_total_roteiro"] == (
        resultado["tempo_total_visitas"]
        + resultado["tempo_total_deslocamentos"]
    )

    assert banco.add.call_count == 4
    banco.commit.assert_called_once()


def test_gerar_roteiro_sem_pontos(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros

    banco.scalar.return_value = None
    banco.scalars.return_value.all.return_value = []

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados_roteiro_validos(),
    )

    assert resposta.status_code == 404
    banco.commit.assert_not_called()


def test_gerar_roteiro_sem_atracoes_compativeis(
    ambiente_roteiros,
):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)

    dados = dados_roteiro_validos()
    dados["orcamento_maximo"] = 0
    dados["tempo_disponivel_minutos"] = 30

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados,
    )

    assert resposta.status_code == 422
    banco.commit.assert_not_called()


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("tempo_disponivel_minutos", 0),
        ("tempo_disponivel_minutos", -1),
        ("orcamento_maximo", -1),
        ("orcamento_maximo", -0.01),
        ("data_visita", "data-invalida"),
    ],
)
def test_rejeitar_dados_invalidos(
    ambiente_roteiros, campo, valor
):
    cliente, banco, usuario = ambiente_roteiros

    dados = dados_roteiro_validos()
    dados[campo] = valor

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados,
    )

    assert resposta.status_code == 422
    banco.commit.assert_not_called()


def test_erro_ao_salvar_roteiro(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)

    banco.commit.side_effect = Exception(
        "Falha simulada no banco"
    )

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados_roteiro_validos(),
    )

    assert resposta.status_code == 500
    banco.rollback.assert_called_once()


# ==========================================
# CONSULTA DE ROTEIROS
# ==========================================

def test_listar_roteiros(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros

    roteiro = SimpleNamespace(
        id=uuid4(),
        usuario_id=usuario.id,
        data_inicio=date(2026, 11, 24),
        data_fim=date(2026, 11, 24),
        custo_total_estimado=100.0,
    )

    banco.scalars.return_value.all.return_value = [
        roteiro,
    ]

    resposta = cliente.get("/roteiros")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["id"] == str(roteiro.id)


def test_listar_roteiros_vazio(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros

    banco.scalars.return_value.all.return_value = []

    resposta = cliente.get("/roteiros")

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_consultar_roteiro_salvo(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros

    poi = criar_ponto("Museu", "Museu", 30, 120, 4.9)

    visita = SimpleNamespace(
        poi_id=poi.id,
        ordem_sequencia=1,
        tempo_deslocamento_previsto=0,
        distancia_deslocamento_metros=0.0,
    )

    dia = SimpleNamespace(
        data_referencia=date(2026, 11, 24),
        tempo_disponivel_minutos=360,
        atividades=[visita],
    )

    roteiro = SimpleNamespace(
        id=uuid4(),
        usuario_id=usuario.id,
        data_inicio=date(2026, 11, 24),
        data_fim=date(2026, 11, 24),
        custo_total_estimado=30.0,
        dias=[dia],
    )

    banco.scalar.return_value = roteiro
    banco.get.return_value = poi

    resposta = cliente.get(
        f"/roteiros/{roteiro.id}"
    )

    assert resposta.status_code == 200

    resultado = resposta.json()

    assert resultado["id"] == str(roteiro.id)
    assert len(resultado["dias"]) == 1
    assert len(resultado["dias"][0]["atividades"]) == 1
    assert (
        resultado["dias"][0]["atividades"][0]["nome"]
        == "Museu"
    )


def test_consultar_roteiro_inexistente(
    ambiente_roteiros,
):
    cliente, banco, usuario = ambiente_roteiros

    banco.scalar.return_value = None

    resposta = cliente.get(
        f"/roteiros/{uuid4()}"
    )

    assert resposta.status_code == 404


def test_consultar_roteiro_de_outro_usuario(
    ambiente_roteiros,
):
    cliente, banco, usuario = ambiente_roteiros

    # A consulta filtrada por usuario deve retornar None
    # quando o roteiro nao pertence ao usuario atual.
    banco.scalar.return_value = None

    resposta = cliente.get(
        f"/roteiros/{uuid4()}"
    )

    assert resposta.status_code == 404
    banco.get.assert_not_called()


def test_geracao_retorna_deslocamentos_por_atividade(
    ambiente_roteiros,
):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados_roteiro_validos(),
    )

    assert resposta.status_code == 201

    resultado = resposta.json()
    atividades = resultado["atividades"]

    assert len(atividades) == 2

    # A primeira atraÃ§Ã£o nÃ£o possui deslocamento anterior.
    assert atividades[0]["tempo_deslocamento_previsto"] == 0
    assert atividades[0]["distancia_deslocamento_metros"] == 0

    # A segunda atraÃ§Ã£o deve conter o deslocamento calculado.
    assert atividades[1]["tempo_deslocamento_previsto"] > 0
    assert atividades[1]["distancia_deslocamento_metros"] > 0

    # O total de deslocamentos deve corresponder
    # Ã  soma dos deslocamentos das atividades.
    assert resultado["tempo_total_deslocamentos"] == sum(
        atividade["tempo_deslocamento_previsto"]
        for atividade in atividades
    )
