from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Protocol
from uuid import UUID

from app.services.calculadora_deslocamentos import (
    calcular_distancia_metros,
    estimar_tempo_deslocamento,
)
from app.services.gerador_roteiros import selecionar_pontos_interesse
from app.services.pocs.matriz_deslocamentos import obter_matriz_deslocamentos
from app.services.pocs.otimizacao import otimizar_rota
from app.services.pocs.recomendacao import rankear_pontos
from app.services.qualidade_pois import nome_poi_e_util


class PontoPlanejavel(Protocol):
    id: UUID
    nome: str
    categoria: str | None
    preco_estimado: float | None
    duracao_minutos: int | None
    avaliacao_media: float | None


@dataclass(frozen=True)
class AtividadePlanejada:
    ponto: PontoPlanejavel
    tempo_deslocamento: int
    distancia_deslocamento_metros: float


@dataclass(frozen=True)
class PlanoRoteiro:
    atividades: list[AtividadePlanejada]
    custo_total: float
    tempo_visitas: int
    tempo_deslocamentos: int
    fonte_matriz: str

    @property
    def tempo_total(self) -> int:
        return self.tempo_visitas + self.tempo_deslocamentos


def _criar_plano_guloso(
    pontos: list[PontoPlanejavel],
    orcamento_maximo: float,
    tempo_disponivel_minutos: int,
    interesses: list[str],
    coordenadas: dict[UUID, tuple[float, float]],
    metrica_recomendacao: str,
    peso_cosseno: float,
) -> PlanoRoteiro:
    selecionados, custo_total, _ = selecionar_pontos_interesse(
        pontos=pontos,
        orcamento_maximo=orcamento_maximo,
        tempo_disponivel_minutos=tempo_disponivel_minutos,
        interesses=interesses,
        coordenadas=coordenadas,
        metrica_recomendacao=metrica_recomendacao,
        peso_cosseno=peso_cosseno,
    )
    atividades: list[AtividadePlanejada] = []
    ponto_anterior: PontoPlanejavel | None = None

    for ponto in selecionados:
        distancia = 0.0
        tempo = 0
        if ponto_anterior is not None:
            origem = coordenadas.get(ponto_anterior.id)
            destino = coordenadas.get(ponto.id)
            if origem is not None and destino is not None:
                distancia = calcular_distancia_metros(*origem, *destino)
                tempo = estimar_tempo_deslocamento(distancia)
        atividades.append(AtividadePlanejada(ponto, tempo, distancia))
        ponto_anterior = ponto

    tempo_visitas = sum(int(item.ponto.duracao_minutos or 0) for item in atividades)
    tempo_deslocamentos = sum(item.tempo_deslocamento for item in atividades)
    return PlanoRoteiro(
        atividades=atividades,
        custo_total=custo_total,
        tempo_visitas=tempo_visitas,
        tempo_deslocamentos=tempo_deslocamentos,
        fonte_matriz="haversine",
    )


def _zerar_retorno_ao_deposito(matriz: list[list[int]]) -> list[list[int]]:
    matriz_aberta = [linha.copy() for linha in matriz]
    for linha in matriz_aberta:
        linha[0] = 0
    return matriz_aberta


def _criar_plano_otimizado(
    pontos: list[PontoPlanejavel],
    orcamento_maximo: float,
    tempo_disponivel_minutos: int,
    interesses: list[str],
    coordenadas: dict[UUID, tuple[float, float]],
    quantidade_paradas: int | None,
    origem: tuple[float, float] | None,
    peso_preferencias: float,
    usar_matriz_viaria: bool,
    metrica_recomendacao: str,
    peso_cosseno: float,
    retornar_origem: bool,
) -> PlanoRoteiro:
    candidatos_validos = [
        ponto
        for ponto in pontos
        if ponto.preco_estimado is not None
        and 0 <= ponto.preco_estimado <= orcamento_maximo
        and ponto.duracao_minutos is not None
        and 0 < ponto.duracao_minutos <= tempo_disponivel_minutos
    ]
    ranking = rankear_pontos(
        candidatos_validos, interesses, metrica_recomendacao, peso_cosseno
    )[:19]
    candidatos = [item.ponto for item in ranking]
    if len(candidatos) < (quantidade_paradas or 1):
        return PlanoRoteiro([], 0.0, 0, 0, "indisponivel")

    matriz = obter_matriz_deslocamentos(
        coordenadas=[coordenadas[ponto.id] for ponto in candidatos],
        origem=origem,
        usar_osrm=usar_matriz_viaria,
    )
    duracoes = [0, *(int(ponto.duracao_minutos or 0) for ponto in candidatos)]
    afinidades = [0.0, *(item.afinidade for item in ranking)]
    valores = [Decimal(str(ponto.preco_estimado)) for ponto in candidatos]
    soma_valores = sum(valores)
    teto = min(Decimal(str(orcamento_maximo)), soma_valores)
    # Preserva a precisão dos valores enquanto a soma couber nos inteiros do solver.
    casas = min(
        max(-valor.as_tuple().exponent for valor in [*valores, teto]),
        16 - soma_valores.adjusted(),
    )
    precos = [0, *(
        int(valor.scaleb(casas).to_integral_value(rounding=ROUND_CEILING))
        for valor in valores
    )]
    orcamento = int(teto.scaleb(casas).to_integral_value(rounding=ROUND_FLOOR))
    matriz_otimizacao = (
        matriz.tempos_minutos
        if retornar_origem
        else _zerar_retorno_ao_deposito(matriz.tempos_minutos)
    )
    rota = otimizar_rota(
        matriz_minutos=matriz_otimizacao,
        duracoes_minutos=duracoes,
        afinidades=afinidades,
        quantidade_paradas=quantidade_paradas,
        limite_minutos=tempo_disponivel_minutos,
        precos_centavos=precos,
        orcamento_centavos=orcamento,
        peso_preferencias=peso_preferencias,
    )

    atividades: list[AtividadePlanejada] = []
    indice_anterior = 0
    for indice in rota[1:-1]:
        ponto = candidatos[indice - 1]
        atividades.append(
            AtividadePlanejada(
                ponto=ponto,
                tempo_deslocamento=matriz.tempos_minutos[indice_anterior][indice],
                distancia_deslocamento_metros=(
                    matriz.distancias_metros[indice_anterior][indice]
                ),
            )
        )
        indice_anterior = indice

    tempo_retorno = matriz.tempos_minutos[indice_anterior][0] if retornar_origem else 0

    return PlanoRoteiro(
        atividades=atividades,
        custo_total=float(sum(valores[indice - 1] for indice in rota[1:-1])),
        tempo_visitas=sum(int(item.ponto.duracao_minutos or 0) for item in atividades),
        tempo_deslocamentos=(
            sum(item.tempo_deslocamento for item in atividades)
            + tempo_retorno
        ),
        fonte_matriz=matriz.fonte,
    )


def planejar_roteiro(
    pontos: list[PontoPlanejavel],
    orcamento_maximo: float,
    tempo_disponivel_minutos: int,
    interesses: list[str],
    coordenadas: dict[UUID, tuple[float, float]],
    quantidade_paradas: int | None = None,
    origem: tuple[float, float] | None = None,
    peso_preferencias: float | None = None,
    usar_matriz_viaria: bool = False,
    metrica_recomendacao: str = "cosseno",
    peso_cosseno: float = 0.7,
    retornar_origem: bool = False,
) -> PlanoRoteiro:
    pontos_validos = [
        ponto for ponto in pontos
        if ponto.id in coordenadas and nome_poi_e_util(ponto.nome)
    ]
    if (
        quantidade_paradas is None
        and origem is None
        and peso_preferencias is None
        and not usar_matriz_viaria
    ):
        return _criar_plano_guloso(
            pontos_validos,
            orcamento_maximo,
            tempo_disponivel_minutos,
            interesses,
            coordenadas,
            metrica_recomendacao,
            peso_cosseno,
        )
    return _criar_plano_otimizado(
        pontos_validos,
        orcamento_maximo,
        tempo_disponivel_minutos,
        interesses,
        coordenadas,
        quantidade_paradas,
        origem,
        0.8 if peso_preferencias is None else peso_preferencias,
        usar_matriz_viaria,
        metrica_recomendacao,
        peso_cosseno,
        retornar_origem,
    )
