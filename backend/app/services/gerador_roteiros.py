
from app.models.domain_models import PontoDeInteresse


def selecionar_pontos_interesse(
    pontos: list[PontoDeInteresse],
    orcamento_maximo: float,
    tempo_disponivel_minutos: int,
    interesses: list[str] | None = None
) -> tuple[list[PontoDeInteresse], float, int]:
    """
    Seleciona atrações considerando:
    - interesses do usuário
    - avaliações dos pontos turísticos
    - orçamento máximo
    - tempo disponível

    Retorna:
    - atrações selecionadas
    - custo total estimado
    - tempo total de visitas
    """

    # 1. Filtra atrações com dados válidos
    pontos_validos = [
        ponto
        for ponto in pontos
        if ponto.preco_estimado is not None
        and ponto.duracao_minutos is not None
        and ponto.preco_estimado >= 0
        and ponto.duracao_minutos > 0
    ]

    # 2. Normaliza os interesses do usuário
    interesses_normalizados = {
        interesse.strip().casefold()
        for interesse in (interesses or [])
        if interesse.strip()
    }

    # 3. Verifica se a categoria corresponde
    # aos interesses cadastrados
    def corresponde_interesse(ponto: PontoDeInteresse) -> bool:
        if not ponto.categoria:
            return False

        categoria = ponto.categoria.strip().casefold()

        return categoria in interesses_normalizados

    # 4. Prioriza interesses e depois avaliações
    pontos_ordenados = sorted(
        pontos_validos,
        key=lambda ponto: (
            corresponde_interesse(ponto),
            ponto.avaliacao_media or 0
        ),
        reverse=True
    )

    # 5. Seleciona atrações respeitando os limites
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
