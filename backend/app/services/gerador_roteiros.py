from uuid import UUID

from app.models.domain_models import PontoDeInteresse
from app.services.calculadora_deslocamentos import (
    calcular_distancia_metros,
    estimar_tempo_deslocamento
)
from app.services.pocs.recomendacao import rankear_pontos


def selecionar_pontos_interesse(
    pontos: list[PontoDeInteresse],
    orcamento_maximo: float,
    tempo_disponivel_minutos: int,
    interesses: list[str] | None = None,
    coordenadas: dict[UUID, tuple[float, float]] | None = None,
    metrica_recomendacao: str = "cosseno",
    peso_cosseno: float = 0.7,
) -> tuple[list[PontoDeInteresse], float, int]:
    """
    Seleciona atrações considerando:
    - interesses do usuário
    - avaliações dos pontos turísticos
    - orçamento máximo
    - duração das visitas
    - tempo estimado de deslocamento

    Retorna:
    - atrações selecionadas
    - custo total estimado
    - tempo total (visitas + deslocamentos)
    """

    pontos_validos = [
        ponto
        for ponto in pontos
        if ponto.preco_estimado is not None
        and ponto.duracao_minutos is not None
        and ponto.preco_estimado >= 0
        and ponto.duracao_minutos > 0
    ]

    pontos_ordenados = [
        item.ponto
        for item in rankear_pontos(
            pontos_validos,
            interesses or [],
            metrica_recomendacao,
            peso_cosseno,
        )
    ]

    selecionados = []
    custo_total = 0.0
    tempo_total = 0

    for ponto in pontos_ordenados:
        tempo_deslocamento = 0

        # Calcula deslocamento a partir da última atração
        if selecionados and coordenadas:
            ponto_anterior = selecionados[-1]

            origem = coordenadas.get(ponto_anterior.id)
            destino = coordenadas.get(ponto.id)

            if origem is not None and destino is not None:
                distancia = calcular_distancia_metros(
                    origem[0],
                    origem[1],
                    destino[0],
                    destino[1]
                )

                tempo_deslocamento = estimar_tempo_deslocamento(
                    distancia
                )

        novo_custo = custo_total + ponto.preco_estimado

        novo_tempo = (
            tempo_total
            + tempo_deslocamento
            + ponto.duracao_minutos
        )

        if (
            novo_custo <= orcamento_maximo
            and novo_tempo <= tempo_disponivel_minutos
        ):
            selecionados.append(ponto)
            custo_total = novo_custo
            tempo_total = novo_tempo

    return selecionados, custo_total, tempo_total
