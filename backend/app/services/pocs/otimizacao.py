from __future__ import annotations

import sys
import time


class RotaInviavelError(RuntimeError):
    pass


def _validar_matriz(matriz: list[list[int]]) -> None:
    tamanho = len(matriz)
    if tamanho < 2 or any(len(linha) != tamanho for linha in matriz):
        raise ValueError("Matriz de deslocamentos inválida.")
    if any(valor < 0 for linha in matriz for valor in linha):
        raise ValueError("Matriz de deslocamentos contém valor negativo.")


def _otimizar_rota_portatil(
    matriz_minutos: list[list[int]],
    duracoes_minutos: list[int],
    afinidades: list[float],
    quantidade_paradas: int | None,
    limite_minutos: int,
    precos_centavos: list[int],
    orcamento_centavos: int,
    peso_preferencias: float,
    segundos: int,
) -> list[int]:
    """Fallback para Windows, onde importar OR-Tools bloqueia o asyncio."""
    inicio = time.monotonic()
    estados = [([0], frozenset(), 0, 0, 0.0)]
    limite_estados = 5_000
    limite_paradas = quantidade_paradas or (len(matriz_minutos) - 1)
    melhor = None

    for profundidade in range(1, limite_paradas + 1):
        proximos = []
        for rota, usados, tempo_atual, custo_atual, pontuacao in estados:
            origem = rota[-1]
            for destino in range(1, len(matriz_minutos)):
                if destino in usados:
                    continue
                novo_tempo = (
                    tempo_atual
                    + matriz_minutos[origem][destino]
                    + duracoes_minutos[destino]
                )
                novo_custo = custo_atual + precos_centavos[destino]
                if novo_tempo > limite_minutos or novo_custo > orcamento_centavos:
                    continue
                deslocamento_relativo = (
                    matriz_minutos[origem][destino] / max(1, limite_minutos)
                )
                nova_pontuacao = (
                    pontuacao
                    + peso_preferencias * afinidades[destino] / limite_paradas
                    - (1 - peso_preferencias) * deslocamento_relativo
                )
                nova_rota = [*rota, destino]
                proximos.append((
                    nova_rota,
                    usados | {destino},
                    novo_tempo,
                    novo_custo,
                    nova_pontuacao,
                ))
                tempo_retorno = matriz_minutos[destino][0]
                if (
                    (quantidade_paradas is None or profundidade == quantidade_paradas)
                    and novo_tempo + tempo_retorno <= limite_minutos
                ):
                    pontuacao_final = nova_pontuacao - (
                        (1 - peso_preferencias) * tempo_retorno / limite_minutos
                    )
                    candidato = (
                        -profundidade, -pontuacao_final, novo_tempo + tempo_retorno,
                        novo_custo, nova_rota,
                    )
                    if melhor is None or candidato < melhor:
                        melhor = candidato
            if time.monotonic() - inicio >= max(1, segundos):
                break
        if not proximos:
            break
        proximos.sort(key=lambda estado: (-estado[4], estado[2], estado[3], estado[0]))
        estados = proximos[:limite_estados]

    if melhor is None:
        raise RotaInviavelError(
            "Nenhuma rota atende simultaneamente ao tempo, orçamento e número de paradas."
        )
    return [*melhor[-1], 0]


def otimizar_rota(
    matriz_minutos: list[list[int]],
    duracoes_minutos: list[int],
    afinidades: list[float],
    quantidade_paradas: int | None,
    limite_minutos: int,
    precos_centavos: list[int] | None = None,
    orcamento_centavos: int | None = None,
    peso_preferencias: float = 0.8,
    segundos: int = 5,
) -> list[int]:
    _validar_matriz(matriz_minutos)
    tamanho = len(matriz_minutos)
    if len(duracoes_minutos) != tamanho or len(afinidades) != tamanho:
        raise ValueError("Durações e afinidades devem corresponder à matriz.")
    if quantidade_paradas is not None and not 1 <= quantidade_paradas < tamanho:
        raise ValueError("Quantidade de paradas inválida.")
    if limite_minutos <= 0 or not 0 <= peso_preferencias <= 1:
        raise ValueError("Parâmetros de otimização inválidos.")
    if any(duracao < 0 for duracao in duracoes_minutos):
        raise ValueError("Duração negativa.")

    if (precos_centavos is None) != (orcamento_centavos is None):
        raise ValueError("Preços e orçamento devem ser informados em conjunto.")
    if precos_centavos is not None:
        if len(precos_centavos) != tamanho or any(preco < 0 for preco in precos_centavos):
            raise ValueError("Preços inválidos.")
        if orcamento_centavos is None or orcamento_centavos < 0:
            raise ValueError("Orçamento inválido.")

    precos_normalizados = precos_centavos or [0] * tamanho
    orcamento_normalizado = (
        orcamento_centavos
        if orcamento_centavos is not None
        else sum(precos_normalizados)
    )
    if sys.platform == "win32":
        return _otimizar_rota_portatil(
            matriz_minutos,
            duracoes_minutos,
            afinidades,
            quantidade_paradas,
            limite_minutos,
            precos_normalizados,
            orcamento_normalizado,
            peso_preferencias,
            segundos,
        )

    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    manager = pywrapcp.RoutingIndexManager(tamanho, 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    no = manager.IndexToNode
    escala = 1_000_000
    referencia_minutos = max(1, limite_minutos)

    def custo(origem_indice: int, destino_indice: int) -> int:
        origem = no(origem_indice)
        destino = no(destino_indice)
        return round(
            escala
            * (1 - peso_preferencias)
            * matriz_minutos[origem][destino]
            / referencia_minutos
        )

    custo_indice = routing.RegisterTransitCallback(custo)
    routing.SetArcCostEvaluatorOfAllVehicles(custo_indice)

    def tempo(origem_indice: int, destino_indice: int) -> int:
        origem = no(origem_indice)
        destino = no(destino_indice)
        return matriz_minutos[origem][destino] + duracoes_minutos[origem]

    tempo_indice = routing.RegisterTransitCallback(tempo)
    routing.AddDimension(tempo_indice, 0, limite_minutos, True, "TempoTotal")

    def contar_visita(origem_indice: int, _destino_indice: int) -> int:
        return int(no(origem_indice) != 0)

    visitas_indice = routing.RegisterTransitCallback(contar_visita)
    limite_paradas = quantidade_paradas or (tamanho - 1)
    routing.AddDimension(visitas_indice, 0, limite_paradas, True, "NumeroVisitas")
    minimo_paradas = quantidade_paradas or 1
    routing.GetDimensionOrDie("NumeroVisitas").CumulVar(routing.End(0)).SetMin(minimo_paradas)

    if precos_centavos is not None and orcamento_centavos is not None:
        def preco(origem_indice: int) -> int:
            return precos_centavos[no(origem_indice)]

        preco_indice = routing.RegisterUnaryTransitCallback(preco)
        routing.AddDimension(preco_indice, 0, orcamento_centavos, True, "Orcamento")

    for indice in range(1, tamanho):
        afinidade = max(0.0, min(1.0, afinidades[indice]))
        penalidade = 2 * escala + round(escala * peso_preferencias * afinidade / limite_paradas)
        routing.AddDisjunction([manager.NodeToIndex(indice)], penalidade)

    busca = pywrapcp.DefaultRoutingSearchParameters()
    busca.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    busca.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    busca.time_limit.seconds = max(1, segundos)

    solucao = routing.SolveWithParameters(busca)
    if solucao is None:
        raise RotaInviavelError(
            "Nenhuma rota atende simultaneamente ao tempo, orçamento e número de paradas."
        )

    rota: list[int] = []
    indice = routing.Start(0)
    while not routing.IsEnd(indice):
        rota.append(no(indice))
        indice = solucao.Value(routing.NextVar(indice))
    rota.append(0)
    return rota
