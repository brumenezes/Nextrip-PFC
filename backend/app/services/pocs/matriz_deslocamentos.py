from __future__ import annotations

import math
import os
from dataclasses import dataclass

import httpx

from app.services.calculadora_deslocamentos import (
    calcular_distancia_metros,
    estimar_tempo_deslocamento,
)


Coordenada = tuple[float, float]


@dataclass(frozen=True)
class MatrizDeslocamentos:
    tempos_minutos: list[list[int]]
    distancias_metros: list[list[float]]
    fonte: str


def _adicionar_origem_virtual(matriz: MatrizDeslocamentos) -> MatrizDeslocamentos:
    tamanho = len(matriz.tempos_minutos) + 1
    tempos = [[0 for _ in range(tamanho)]]
    distancias = [[0.0 for _ in range(tamanho)]]
    for linha_tempo, linha_distancia in zip(
        matriz.tempos_minutos,
        matriz.distancias_metros,
        strict=True,
    ):
        tempos.append([0, *linha_tempo])
        distancias.append([0.0, *linha_distancia])
    return MatrizDeslocamentos(tempos, distancias, matriz.fonte)


def _validar_coordenada(coordenada: Coordenada) -> None:
    latitude, longitude = coordenada
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude ou longitude inválida.")


def matriz_haversine(
    coordenadas: list[Coordenada],
    origem_virtual: bool = False,
) -> MatrizDeslocamentos:
    for coordenada in coordenadas:
        _validar_coordenada(coordenada)

    tamanho = len(coordenadas) + int(origem_virtual)
    tempos = [[0 for _ in range(tamanho)] for _ in range(tamanho)]
    distancias = [[0.0 for _ in range(tamanho)] for _ in range(tamanho)]
    deslocamento_indice = int(origem_virtual)

    for origem_indice, origem in enumerate(coordenadas, start=deslocamento_indice):
        for destino_indice, destino in enumerate(coordenadas, start=deslocamento_indice):
            if origem_indice == destino_indice:
                continue
            distancia = calcular_distancia_metros(*origem, *destino)
            distancias[origem_indice][destino_indice] = distancia
            tempos[origem_indice][destino_indice] = estimar_tempo_deslocamento(distancia)

    return MatrizDeslocamentos(tempos, distancias, "haversine")


def matriz_osrm(
    coordenadas: list[Coordenada],
    cliente: httpx.Client | None = None,
) -> MatrizDeslocamentos:
    if not 2 <= len(coordenadas) <= 20:
        raise ValueError("A matriz OSRM aceita entre 2 e 20 coordenadas.")
    for coordenada in coordenadas:
        _validar_coordenada(coordenada)

    coordenadas_url = ";".join(
        f"{longitude},{latitude}"
        for latitude, longitude in coordenadas
    )
    base_url = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")
    cliente_proprio = cliente is None
    cliente = cliente or httpx.Client(timeout=15.0)

    try:
        resposta = cliente.get(
            f"{base_url}/table/v1/driving/{coordenadas_url}",
            params={"annotations": "duration,distance"},
            headers={"User-Agent": "Nextrip/1.0"},
        )
        resposta.raise_for_status()
        payload = resposta.json()
    finally:
        if cliente_proprio:
            cliente.close()

    if not isinstance(payload, dict):
        raise RuntimeError("OSRM retornou uma resposta inválida.")
    if payload.get("code") != "Ok":
        raise RuntimeError(f"OSRM indisponível: {payload.get('message', payload.get('code'))}")

    duracoes = payload.get("durations")
    distancias = payload.get("distances")
    tamanho = len(coordenadas)
    if (
        not isinstance(duracoes, list)
        or not isinstance(distancias, list)
        or len(duracoes) != tamanho
        or len(distancias) != tamanho
    ):
        raise RuntimeError("OSRM retornou uma matriz incompatível.")

    tempos_convertidos: list[list[int]] = []
    distancias_convertidas: list[list[float]] = []
    for linha_duracoes, linha_distancias in zip(duracoes, distancias, strict=True):
        if (
            not isinstance(linha_duracoes, list)
            or not isinstance(linha_distancias, list)
            or len(linha_duracoes) != tamanho
            or len(linha_distancias) != tamanho
        ):
            raise RuntimeError("OSRM retornou uma matriz incompatível.")
        if any(valor is None for valor in linha_duracoes + linha_distancias):
            raise RuntimeError("OSRM não encontrou rota entre todos os pontos.")
        if any(
            type(valor) not in (int, float) or not math.isfinite(valor) or valor < 0
            for valor in linha_duracoes + linha_distancias
        ):
            raise RuntimeError("OSRM retornou um deslocamento inválido.")

        tempos_convertidos.append([
            0 if valor == 0 else max(1, math.ceil(float(valor) / 60))
            for valor in linha_duracoes
        ])
        distancias_convertidas.append([float(valor) for valor in linha_distancias])

    return MatrizDeslocamentos(tempos_convertidos, distancias_convertidas, "osrm")


def obter_matriz_deslocamentos(
    coordenadas: list[Coordenada],
    origem: Coordenada | None,
    usar_osrm: bool = True,
    cliente: httpx.Client | None = None,
) -> MatrizDeslocamentos:
    if origem is None:
        if usar_osrm and len(coordenadas) >= 2:
            try:
                return _adicionar_origem_virtual(matriz_osrm(coordenadas, cliente))
            except (httpx.HTTPError, RuntimeError, ValueError, OverflowError):
                pass
        return matriz_haversine(coordenadas, origem_virtual=True)

    todas_coordenadas = [origem, *coordenadas]
    if usar_osrm:
        try:
            return matriz_osrm(todas_coordenadas, cliente)
        except (httpx.HTTPError, RuntimeError, ValueError, OverflowError):
            pass
    return matriz_haversine(todas_coordenadas)
