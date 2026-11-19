import pytest

from app.services.calculadora_deslocamentos import (
    calcular_distancia_metros,
    estimar_tempo_deslocamento,
)


@pytest.mark.parametrize(
    "distancia_metros, velocidade_kmh, tempo_esperado",
    [
        (0, 30, 0),
        (1000, 30, 2),
        (1500, 30, 3),
        (1000, 60, 1),
        (100, 30, 1),
    ],
)
def test_estimativa_tempo_valida(
    distancia_metros,
    velocidade_kmh,
    tempo_esperado,
):
    resultado = estimar_tempo_deslocamento(
        distancia_metros,
        velocidade_kmh,
    )

    assert resultado == tempo_esperado


@pytest.mark.parametrize(
    "distancia_metros, velocidade_kmh",
    [
        (-1, 30),
        (-100, 30),
        (1000, 0),
        (1000, -10),
    ],
)
def test_estimativa_tempo_invalida(
    distancia_metros,
    velocidade_kmh,
):
    with pytest.raises(ValueError):
        estimar_tempo_deslocamento(
            distancia_metros,
            velocidade_kmh,
        )


def test_distancia_entre_coordenadas_iguais():
    resultado = calcular_distancia_metros(
        -23.5855,
        -46.6097,
        -23.5855,
        -46.6097,
    )

    assert resultado == pytest.approx(0)


def test_distancia_entre_coordenadas_diferentes():
    resultado = calcular_distancia_metros(
        -23.5855,
        -46.6097,
        -23.5614,
        -46.6559,
    )

    assert 5000 < resultado < 6000
