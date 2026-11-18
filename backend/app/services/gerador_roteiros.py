
from app.models.domain_models import PontoDeInteresse


def selecionar_pontos_interesse(
    pontos: list[PontoDeInteresse],
    orcamento_maximo: float,
    tempo_disponivel_minutos: int
) -> tuple[list[PontoDeInteresse], float, int]:
    """
    Seleciona atrações respeitando o orçamento
    e o tempo disponível para visitas.

    Retorna:
    - atrações selecionadas
    - custo total estimado
    - tempo total de visitas
    """

    pontos_validos = [
        ponto
        for ponto in pontos
        if ponto.preco_estimado is not None
        and ponto.duracao_minutos is not None
        and ponto.preco_estimado >= 0
        and ponto.duracao_minutos > 0
    ]

    # Prioriza as atrações com melhores avaliações
    pontos_ordenados = sorted(
        pontos_validos,
        key=lambda ponto: ponto.avaliacao_media or 0,
        reverse=True
    )

    selecionados = []
    custo_total = 0.0
    tempo_total = 0

    for ponto in pontos_ordenados:
        novo_custo = custo_total + ponto.preco_estimado
        novo_tempo = tempo_total + ponto.duracao_minutos

        if (
            novo_custo <= orcamento_maximo
            and novo_tempo <= tempo_disponivel_minutos
        ):
            selecionados.append(ponto)
            custo_total = novo_custo
            tempo_total = novo_tempo

    return selecionados, custo_total, tempo_total
