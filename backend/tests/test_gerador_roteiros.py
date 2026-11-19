from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.gerador_roteiros import selecionar_pontos_interesse


def criar_ponto(nome, categoria, preco, duracao, avaliacao=4.5):
    """Cria uma atraÃ§Ã£o fictÃ­cia para os testes."""
    return SimpleNamespace(
        id=uuid4(),
        nome=nome,
        categoria=categoria,
        preco_estimado=preco,
        duracao_minutos=duracao,
        avaliacao_media=avaliacao,
    )


@pytest.mark.parametrize(
    "orcamento, quantidade_esperada, custo_esperado",
    [
        (0, 1, 0),
        (30, 2, 30),
        (50, 2, 30),
        (100, 3, 100),
    ],
)
def test_limite_orcamento(
    orcamento, quantidade_esperada, custo_esperado
):
    pontos = [
        criar_ponto("Museu", "Museu", 30, 60, 4.9),
        criar_ponto("Parque", "Parque", 0, 60, 4.8),
        criar_ponto("MASP", "Museu", 70, 60, 4.7),
    ]

    selecionados, custo, tempo = selecionar_pontos_interesse(
        pontos=pontos,
        orcamento_maximo=orcamento,
        tempo_disponivel_minutos=300,
    )

    assert len(selecionados) == quantidade_esperada
    assert custo == custo_esperado
    assert custo <= orcamento


@pytest.mark.parametrize(
    "tempo_disponivel, quantidade_esperada",
    [
        (0, 0),
        (59, 0),
        (60, 1),
        (120, 2),
        (180, 3),
    ],
)
def test_limite_tempo(tempo_disponivel, quantidade_esperada):
    pontos = [
        criar_ponto("Museu", "Museu", 30, 60, 4.9),
        criar_ponto("Parque", "Parque", 0, 60, 4.8),
        criar_ponto("MASP", "Museu", 70, 60, 4.7),
    ]

    selecionados, custo, tempo = selecionar_pontos_interesse(
        pontos=pontos,
        orcamento_maximo=200,
        tempo_disponivel_minutos=tempo_disponivel,
    )

    assert len(selecionados) == quantidade_esperada
    assert tempo <= tempo_disponivel


def test_prioriza_interesses_usuario():
    pontos = [
        criar_ponto("Parque", "Parque", 0, 60, 5.0),
        criar_ponto("Museu", "Museu", 30, 60, 4.0),
    ]

    selecionados, _, _ = selecionar_pontos_interesse(
        pontos=pontos,
        orcamento_maximo=100,
        tempo_disponivel_minutos=120,
        interesses=["Museu"],
    )

    assert selecionados[0].categoria == "Museu"


def test_ignora_pontos_invalidos():
    pontos = [
        criar_ponto("VÃ¡lido", "Museu", 30, 60),
        criar_ponto("PreÃ§o negativo", "Museu", -10, 60),
        criar_ponto("DuraÃ§Ã£o zero", "Parque", 0, 0),
        criar_ponto("PreÃ§o ausente", "Museu", None, 60),
    ]

    selecionados, custo, tempo = selecionar_pontos_interesse(
        pontos=pontos,
        orcamento_maximo=100,
        tempo_disponivel_minutos=300,
    )

    assert len(selecionados) == 1
    assert selecionados[0].nome == "VÃ¡lido"
    assert custo == 30
    assert tempo == 60


def test_considera_deslocamento_no_tempo():
    museu = criar_ponto("Museu", "Museu", 30, 60, 4.9)
    parque = criar_ponto("Parque", "Parque", 0, 60, 4.8)

    coordenadas = {
        museu.id: (-23.5855, -46.6097),
        parque.id: (-23.5874, -46.6576),
    }

    selecionados, _, tempo = selecionar_pontos_interesse(
        pontos=[museu, parque],
        orcamento_maximo=100,
        tempo_disponivel_minutos=120,
        coordenadas=coordenadas,
    )

    # Duas visitas exigiriam 120 minutos,
    # sem contar o deslocamento.
    assert len(selecionados) == 1
    assert tempo == 60


def test_retorna_vazio_sem_pontos():
    selecionados, custo, tempo = selecionar_pontos_interesse(
        pontos=[],
        orcamento_maximo=100,
        tempo_disponivel_minutos=300,
    )

    assert selecionados == []
    assert custo == 0
    assert tempo == 0


def test_ponto_sem_categoria():
    pontos = [
        criar_ponto("AtraÃ§Ã£o sem categoria", None, 0, 60, 4.9),
        criar_ponto("Museu", "Museu", 30, 60, 4.5),
    ]

    selecionados, custo, tempo = selecionar_pontos_interesse(
        pontos=pontos,
        orcamento_maximo=100,
        tempo_disponivel_minutos=120,
        interesses=["Museu"],
    )

    assert len(selecionados) == 2
    assert selecionados[0].nome == "Museu"
    assert custo == 30
    assert tempo == 120
