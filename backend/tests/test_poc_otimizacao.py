from types import SimpleNamespace

import pytest

from app.services.pocs import otimizacao
from app.services.pocs.otimizacao import RotaInviavelError, otimizar_rota


MATRIZ = [
    [0, 5, 5, 10],
    [5, 0, 4, 8],
    [5, 4, 0, 7],
    [10, 8, 7, 0],
]


@pytest.fixture(autouse=True, params=["portatil", "ortools"])
def implementacao_otimizacao(monkeypatch, request):
    plataforma = "win32" if request.param == "portatil" else "linux"
    monkeypatch.setattr(otimizacao, "sys", SimpleNamespace(platform=plataforma))


def test_otimizacao_escolhe_quantidade_exata_e_maior_afinidade():
    rota = otimizar_rota(
        matriz_minutos=MATRIZ,
        duracoes_minutos=[0, 30, 30, 30],
        afinidades=[0.0, 1.0, 0.9, 0.1],
        quantidade_paradas=2,
        limite_minutos=80,
        peso_preferencias=1.0,
        segundos=1,
    )

    assert rota[0] == rota[-1] == 0
    assert len(rota[1:-1]) == 2
    assert set(rota[1:-1]) == {1, 2}


def test_otimizacao_respeita_orcamento():
    rota = otimizar_rota(
        matriz_minutos=MATRIZ,
        duracoes_minutos=[0, 20, 20, 20],
        afinidades=[0.0, 1.0, 0.8, 0.7],
        quantidade_paradas=2,
        limite_minutos=80,
        precos_centavos=[0, 3_000, 2_000, 2_000],
        orcamento_centavos=4_000,
        segundos=1,
    )

    assert set(rota[1:-1]) == {2, 3}


def test_otimizacao_inviavel_quando_tempo_nao_comporta_visita():
    with pytest.raises(RotaInviavelError):
        otimizar_rota(
            matriz_minutos=MATRIZ,
            duracoes_minutos=[0, 60, 60, 60],
            afinidades=[0.0, 1.0, 0.8, 0.7],
            quantidade_paradas=2,
            limite_minutos=30,
            segundos=1,
        )


def test_otimizacao_valida_dimensoes_dos_dados():
    with pytest.raises(ValueError):
        otimizar_rota(
            matriz_minutos=MATRIZ,
            duracoes_minutos=[0, 30],
            afinidades=[0.0, 1.0, 0.8, 0.7],
            quantidade_paradas=2,
            limite_minutos=80,
        )


@pytest.mark.parametrize("peso, esperado", [(0, 2), (0.2, 2), (0.5, 1), (0.8, 1), (1, 1)])
def test_peso_equilibra_afinidade_e_deslocamento(peso, esperado):
    rota = otimizar_rota(
        matriz_minutos=[[0, 60, 1], [0, 0, 1], [0, 1, 0]],
        duracoes_minutos=[0, 10, 10],
        afinidades=[0.0, 1.0, 0.0],
        quantidade_paradas=1,
        limite_minutos=100,
        peso_preferencias=peso,
        segundos=1,
    )
    assert rota == [0, esperado, 0]


def test_rota_fechada_considera_retorno_do_ultimo_ponto():
    rota = otimizar_rota(
        matriz_minutos=[[0, 4, 90], [90, 0, 1], [2, 90, 0]],
        duracoes_minutos=[0, 1, 1],
        afinidades=[0.0, 0.0, 0.0],
        quantidade_paradas=2,
        limite_minutos=10,
        peso_preferencias=0,
        segundos=1,
    )
    assert rota == [0, 1, 2, 0]
