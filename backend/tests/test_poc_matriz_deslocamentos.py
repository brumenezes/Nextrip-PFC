from unittest.mock import MagicMock

import httpx
import pytest

from app.services.pocs.matriz_deslocamentos import (
    matriz_haversine,
    matriz_osrm,
    obter_matriz_deslocamentos,
)


COORDENADAS = [
    (-23.5855, -46.6097),
    (-23.5874, -46.6576),
]


def test_matriz_haversine_com_origem_virtual():
    matriz = matriz_haversine(COORDENADAS, origem_virtual=True)

    assert matriz.fonte == "haversine"
    assert len(matriz.tempos_minutos) == 3
    assert matriz.tempos_minutos[0] == [0, 0, 0]
    assert matriz.tempos_minutos[1][2] > 0
    assert matriz.distancias_metros[1][2] > 0


def test_matriz_osrm_converte_segundos_em_minutos():
    resposta = MagicMock()
    resposta.json.return_value = {
        "code": "Ok",
        "durations": [[0, 61], [119, 0]],
        "distances": [[0, 1000.5], [1001.5, 0]],
    }
    cliente = MagicMock()
    cliente.get.return_value = resposta

    matriz = matriz_osrm(COORDENADAS, cliente=cliente)

    assert matriz.fonte == "osrm"
    assert matriz.tempos_minutos == [[0, 2], [2, 0]]
    assert matriz.distancias_metros[0][1] == 1000.5
    resposta.raise_for_status.assert_called_once()


def test_obter_matriz_faz_fallback_quando_osrm_falha():
    cliente = MagicMock()
    cliente.get.side_effect = httpx.ConnectError("OSRM fora do ar")

    matriz = obter_matriz_deslocamentos(
        COORDENADAS,
        origem=(-23.5505, -46.6333),
        cliente=cliente,
    )

    assert matriz.fonte == "haversine"
    assert len(matriz.tempos_minutos) == 3
    assert matriz.tempos_minutos[0][1] > 0


def test_obter_matriz_osrm_com_origem_virtual():
    resposta = MagicMock()
    resposta.json.return_value = {
        "code": "Ok",
        "durations": [[0, 60], [120, 0]],
        "distances": [[0, 900], [950, 0]],
    }
    cliente = MagicMock()
    cliente.get.return_value = resposta

    matriz = obter_matriz_deslocamentos(COORDENADAS, origem=None, cliente=cliente)

    assert matriz.fonte == "osrm"
    assert matriz.tempos_minutos == [[0, 0, 0], [0, 0, 1], [0, 2, 0]]
    assert matriz.distancias_metros[0] == [0.0, 0.0, 0.0]


@pytest.mark.parametrize("distancias", [
    [[0, -1], [1, 0]],
    [[0, float("nan")], [1, 0]],
    [None, [1, 0]],
])
def test_osrm_invalido_usa_fallback(distancias):
    cliente = MagicMock()
    cliente.get.return_value.json.return_value = {
        "code": "Ok",
        "durations": [[0, 60], [60, 0]],
        "distances": distancias,
    }

    matriz = obter_matriz_deslocamentos(COORDENADAS, origem=None, cliente=cliente)

    assert matriz.fonte == "haversine"
    assert all(valor >= 0 for linha in matriz.distancias_metros for valor in linha)
