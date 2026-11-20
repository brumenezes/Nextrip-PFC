from types import SimpleNamespace

import pytest

from app.services.pocs.recomendacao import (
    decompor_afinidade,
    pontuar_afinidade,
    rankear_pontos,
    similaridade_cosseno,
)


def criar_ponto(nome: str, categoria: str, avaliacao: float):
    return SimpleNamespace(
        nome=nome,
        categoria=categoria,
        avaliacao_media=avaliacao,
    )


def test_afinidade_prioriza_interesse_exato_e_categoria_relacionada():
    afinidade_museu = pontuar_afinidade("Museu", ["museu"])
    afinidade_cultura = pontuar_afinidade("Cultura", ["museu"])
    afinidade_natureza = pontuar_afinidade("Natureza", ["museu"])

    assert afinidade_museu == 1.0
    assert afinidade_cultura > afinidade_natureza


def test_afinidade_normaliza_acentos_espacos_e_hifens():
    assert pontuar_afinidade("Vida Noturna", ["vida-noturna"]) == 1.0


def test_afinidade_sem_interesses_e_zero():
    assert pontuar_afinidade("Museu", []) == 0.0


def test_pontuacao_hibrida_combina_cosseno_e_magnitude():
    detalhes = decompor_afinidade("Cultura", ["Museu"], peso_cosseno=0.6)

    assert detalhes.hibrido == pytest.approx(
        0.6 * detalhes.cosseno + 0.4 * detalhes.compatibilidade_magnitude
    )
    assert pontuar_afinidade("Cultura", ["Museu"], "hibrido", 0.6) == detalhes.hibrido


def test_ranking_combina_afinidade_avaliacao_e_nome():
    parque = criar_ponto("Parque", "Natureza", 5.0)
    museu_b = criar_ponto("Museu B", "Museu", 4.9)
    museu_a = criar_ponto("Museu A", "Museu", 4.9)

    ranking = rankear_pontos([parque, museu_b, museu_a], ["Museu"])

    assert [item.ponto.nome for item in ranking] == [
        "Museu A",
        "Museu B",
        "Parque",
    ]


def test_similaridade_rejeita_vetores_de_tamanhos_diferentes():
    with pytest.raises(ValueError):
        similaridade_cosseno((1.0, 0.0), (1.0,))

