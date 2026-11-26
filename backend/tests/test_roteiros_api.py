from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.core.dependencies import obter_usuario_atual
from app.services.pocs.otimizacao import RotaInviavelError


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


def test_gerar_roteiro_otimizado_com_quantidade_exata(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)
    dados = dados_roteiro_validos()
    dados.update({
        "quantidade_paradas": 1,
        "usar_matriz_viaria": False,
        "metrica_recomendacao": "hibrido",
        "peso_cosseno": 0.7,
    })

    resposta = cliente.post("/roteiros/gerar", json=dados)

    assert resposta.status_code == 201
    resultado = resposta.json()
    assert len(resultado["atividades"]) == 1
    assert resultado["atividades"][0]["nome"] == "Museu"
    assert resultado["tempo_total_roteiro"] <= dados["tempo_disponivel_minutos"]


def test_gerar_roteiro_otimizado_considera_origem(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)
    dados = dados_roteiro_validos()
    dados.update({
        "quantidade_paradas": 1,
        "latitude_origem": -23.5505,
        "longitude_origem": -46.6333,
        "usar_matriz_viaria": False,
    })

    resposta = cliente.post("/roteiros/gerar", json=dados)

    assert resposta.status_code == 201
    atividade = resposta.json()["atividades"][0]
    assert atividade["tempo_deslocamento_previsto"] > 0
    assert atividade["distancia_deslocamento_metros"] > 0


def test_gerar_roteiro_inclui_retorno_ao_ponto_de_partida(ambiente_roteiros):
    cliente, banco, usuario = ambiente_roteiros
    preparar_geracao(banco)
    dados = dados_roteiro_validos()
    dados.update({
        "quantidade_paradas": 1,
        "latitude_origem": -23.5505,
        "longitude_origem": -46.6333,
        "usar_matriz_viaria": False,
        "retornar_origem": True,
    })

    resposta = cliente.post("/roteiros/gerar", json=dados)

    assert resposta.status_code == 201
    resultado = resposta.json()
    deslocamento_ate_atividade = resultado["atividades"][0][
        "tempo_deslocamento_previsto"
    ]
    assert resultado["tempo_total_deslocamentos"] > deslocamento_ate_atividade
    assert resultado["tempo_total_roteiro"] == (
        resultado["tempo_total_visitas"]
        + resultado["tempo_total_deslocamentos"]
    )
    assert resultado["tempo_total_roteiro"] <= dados["tempo_disponivel_minutos"]


@pytest.mark.parametrize("campo, valor", [
    ("latitude_origem", -23.5505),
    ("longitude_origem", -46.6333),
    ("retornar_origem", True),
])
def test_rejeitar_origem_incompleta(ambiente_roteiros, campo, valor):
    cliente, banco, usuario = ambiente_roteiros
    dados = dados_roteiro_validos()
    dados[campo] = valor

    resposta = cliente.post("/roteiros/gerar", json=dados)

    assert resposta.status_code == 422
    banco.commit.assert_not_called()


def test_gerar_roteiro_sem_quantidade_respeita_origem_e_retorno(ambiente_roteiros):
    cliente, banco, _ = ambiente_roteiros
    preparar_geracao(banco)
    dados = dados_roteiro_validos()
    dados.update(latitude_origem=-23.5505, longitude_origem=-46.6333)

    aberta = cliente.post("/roteiros/gerar", json=dados)
    fechada = cliente.post("/roteiros/gerar", json={**dados, "retornar_origem": True})

    assert aberta.status_code == fechada.status_code == 201
    rota_aberta, rota_fechada = aberta.json(), fechada.json()
    for roteiro in (rota_aberta, rota_fechada):
        assert roteiro["tempo_total_roteiro"] <= dados["tempo_disponivel_minutos"]
        assert roteiro["atividades"][0]["tempo_deslocamento_previsto"] > 0
        assert len(roteiro["atividades"]) == 2
        assert roteiro["tempo_total_roteiro"] == (
            roteiro["tempo_total_visitas"] + roteiro["tempo_total_deslocamentos"]
        )
    assert rota_aberta["tempo_total_deslocamentos"] == sum(
        visita["tempo_deslocamento_previsto"] for visita in rota_aberta["atividades"]
    )
    assert rota_fechada["tempo_total_deslocamentos"] > sum(
        visita["tempo_deslocamento_previsto"] for visita in rota_fechada["atividades"]
    )

    banco.commit.reset_mock()
    dados["tempo_disponivel_minutos"] = 120
    assert cliente.post("/roteiros/gerar", json=dados).status_code == 422
    banco.commit.assert_not_called()


def test_gerar_roteiro_legado_filtra_pois_genericos_e_sem_coordenadas(ambiente_roteiros):
    cliente, banco, _ = ambiente_roteiros
    museu, parque = preparar_geracao(banco)
    parque.nome = "  PORTÃO  "
    incompleto = criar_ponto("Casa sem localização", "Museu", 0, 20, 5)
    banco.scalars.return_value.all.return_value.append(incompleto)

    resposta = cliente.post("/roteiros/gerar", json=dados_roteiro_validos())

    assert resposta.status_code == 201
    assert [visita["poi_id"] for visita in resposta.json()["atividades"]] == [str(museu.id)]


@pytest.mark.parametrize("peso, nome", [(0, "Parque"), (1, "Museu")])
def test_peso_preferencias_sem_quantidade_altera_selecao(ambiente_roteiros, peso, nome):
    cliente, banco, _ = ambiente_roteiros
    preparar_geracao(banco)
    dados = dados_roteiro_validos()
    dados.update(
        tempo_disponivel_minutos=140,
        latitude_origem=-23.5874,
        longitude_origem=-46.6576,
        peso_preferencias=peso,
    )

    resposta = cliente.post("/roteiros/gerar", json=dados)

    assert resposta.status_code == 201
    assert [visita["nome"] for visita in resposta.json()["atividades"]] == [nome]


def test_gerar_roteiro_otimizado_rejeita_soma_acima_do_orcamento(ambiente_roteiros):
    cliente, banco, _ = ambiente_roteiros
    museu, parque = preparar_geracao(banco)
    museu.preco_estimado = parque.preco_estimado = 0.014
    dados = dados_roteiro_validos()
    dados.update(orcamento_maximo=0.02, quantidade_paradas=2)

    resposta = cliente.post("/roteiros/gerar", json=dados)

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
        ("peso_preferencias", -0.01),
        ("peso_preferencias", 1.01),
        ("peso_cosseno", -0.01),
        ("peso_cosseno", 1.01),
        ("metrica_recomendacao", "euclidiana"),
        ("quantidade_paradas", 0),
        ("quantidade_paradas", 20),
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


# ==========================================
# TABELA DE DECISAO TD-02
# ==========================================

@pytest.mark.parametrize(
    "cenario, status_esperado, mensagem",
    [
        pytest.param(
            "catalogo_vazio",
            404,
            "Nenhum ponto turístico cadastrado",
            id="TD-02-R1",
        ),
        pytest.param(
            "rota_inviavel",
            422,
            "Rota inviável simulada",
            id="TD-02-R2",
        ),
        pytest.param(
            "sem_atividades",
            422,
            "Nenhuma atração atende ao orçamento e tempo disponíveis",
            id="TD-02-R3",
        ),
        pytest.param(
            "falha_persistencia",
            500,
            "Erro ao salvar o roteiro no banco de dados",
            id="TD-02-R4",
        ),
        pytest.param(
            "sucesso",
            201,
            None,
            id="TD-02-R5",
        ),
    ],
)
def test_tabela_decisao_geracao_roteiro(
    ambiente_roteiros,
    monkeypatch,
    cenario,
    status_esperado,
    mensagem,
):
    cliente, banco, usuario = ambiente_roteiros

    preparar_geracao(banco)
    dados = dados_roteiro_validos()

    if cenario == "catalogo_vazio":
        banco.scalars.return_value.all.return_value = []

    elif cenario == "rota_inviavel":
        planejador_simulado = MagicMock(
            side_effect=RotaInviavelError(
                "Rota inviável simulada"
            )
        )

        monkeypatch.setattr(
            "app.routers.roteiros.planejar_roteiro",
            planejador_simulado,
        )

    elif cenario == "sem_atividades":
        planejador_simulado = MagicMock(
            return_value=SimpleNamespace(
                atividades=[]
            )
        )

        monkeypatch.setattr(
            "app.routers.roteiros.planejar_roteiro",
            planejador_simulado,
        )

    elif cenario == "falha_persistencia":
        banco.commit.side_effect = Exception(
            "Falha simulada no banco"
        )

    resposta = cliente.post(
        "/roteiros/gerar",
        json=dados,
    )

    assert resposta.status_code == status_esperado

    if mensagem is not None:
        assert resposta.json()["detail"] == mensagem

    if cenario in (
        "catalogo_vazio",
        "rota_inviavel",
        "sem_atividades",
    ):
        banco.add.assert_not_called()
        banco.commit.assert_not_called()
        banco.rollback.assert_not_called()

    elif cenario == "falha_persistencia":
        banco.commit.assert_called_once()
        banco.rollback.assert_called_once()
        banco.refresh.assert_not_called()

    elif cenario == "sucesso":
        resultado = resposta.json()

        assert resultado["roteiro_id"]
        assert len(resultado["atividades"]) == 2

        assert (
            resultado["custo_total_estimado"]
            <= dados["orcamento_maximo"]
        )

        assert (
            resultado["tempo_total_roteiro"]
            <= dados["tempo_disponivel_minutos"]
        )

        assert banco.add.call_count == 4

        banco.commit.assert_called_once()
        banco.refresh.assert_called_once()
        banco.rollback.assert_not_called()

    if cenario in ("rota_inviavel", "sem_atividades"):
        planejador_simulado.assert_called_once()