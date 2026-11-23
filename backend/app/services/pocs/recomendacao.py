from __future__ import annotations

import math
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol


DIMENSOES = (
    "cultura",
    "historia",
    "gastronomia",
    "natureza",
    "compras",
    "vida_noturna",
)

PERFIS_CATEGORIA = {
    "museu": (1.0, 0.85, 0.05, 0.05, 0.05, 0.05),
    "galeria": (1.0, 0.35, 0.10, 0.05, 0.10, 0.10),
    "cultura": (1.0, 0.45, 0.10, 0.05, 0.05, 0.15),
    "historia": (0.80, 1.0, 0.05, 0.05, 0.05, 0.05),
    "parque": (0.20, 0.10, 0.05, 1.0, 0.05, 0.05),
    "natureza": (0.15, 0.05, 0.05, 1.0, 0.05, 0.05),
    "mirante": (0.30, 0.10, 0.05, 0.85, 0.05, 0.05),
    "atracao": (0.65, 0.45, 0.15, 0.35, 0.15, 0.10),
    "compras": (0.10, 0.05, 0.40, 0.05, 1.0, 0.20),
    "gastronomia": (0.15, 0.10, 1.0, 0.05, 0.30, 0.20),
    "vida_noturna": (0.15, 0.05, 0.45, 0.05, 0.20, 1.0),
}


class PontoRanqueavel(Protocol):
    categoria: str | None
    avaliacao_media: float | None
    nome: str


@dataclass(frozen=True)
class PontoPontuado:
    ponto: PontoRanqueavel
    afinidade: float


@dataclass(frozen=True)
class PontuacaoAfinidade:
    cosseno: float
    compatibilidade_magnitude: float
    hibrido: float


def normalizar_texto(valor: str) -> str:
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", valor.strip().casefold())
        if not unicodedata.combining(caractere)
    )
    return sem_acentos.replace("-", "_").replace(" ", "_")


def _vetor_categoria(categoria: str | None) -> tuple[float, ...]:
    chave = normalizar_texto(categoria or "atracao")
    return PERFIS_CATEGORIA.get(chave, PERFIS_CATEGORIA["atracao"])


def _vetor_interesses(interesses: Iterable[str]) -> tuple[float, ...]:
    vetor = [0.0] * len(DIMENSOES)

    for interesse in interesses:
        chave = normalizar_texto(interesse)
        if not chave:
            continue

        if chave in DIMENSOES:
            vetor[DIMENSOES.index(chave)] = 1.0

        perfil = PERFIS_CATEGORIA.get(chave)
        if perfil:
            vetor = [max(atual, valor) for atual, valor in zip(vetor, perfil, strict=True)]

    return tuple(vetor)


def similaridade_cosseno(vetor_a: Sequence[float], vetor_b: Sequence[float]) -> float:
    numerador = sum(a * b for a, b in zip(vetor_a, vetor_b, strict=True))
    norma_a = math.sqrt(sum(valor * valor for valor in vetor_a))
    norma_b = math.sqrt(sum(valor * valor for valor in vetor_b))

    if not norma_a or not norma_b:
        return 0.0
    return max(0.0, min(1.0, numerador / (norma_a * norma_b)))


def decompor_afinidade(
    categoria: str | None,
    interesses: Iterable[str],
    peso_cosseno: float = 0.7,
) -> PontuacaoAfinidade:
    if not 0 <= peso_cosseno <= 1:
        raise ValueError("O peso do cosseno deve estar entre zero e um.")
    interesses_normalizados = {
        normalizar_texto(interesse)
        for interesse in interesses
        if interesse.strip()
    }
    categoria_normalizada = normalizar_texto(categoria or "")

    if categoria_normalizada and categoria_normalizada in interesses_normalizados:
        return PontuacaoAfinidade(1.0, 1.0, 1.0)

    perfil = _vetor_interesses(interesses_normalizados)
    perfil_categoria = _vetor_categoria(categoria)
    cosseno = similaridade_cosseno(perfil, perfil_categoria)
    norma_usuario = math.sqrt(sum(valor * valor for valor in perfil))
    norma_categoria = math.sqrt(sum(valor * valor for valor in perfil_categoria))
    maior_norma = max(norma_usuario, norma_categoria)
    magnitude = min(norma_usuario, norma_categoria) / maior_norma if maior_norma else 0.0
    return PontuacaoAfinidade(
        cosseno=cosseno,
        compatibilidade_magnitude=magnitude,
        hibrido=peso_cosseno * cosseno + (1 - peso_cosseno) * magnitude,
    )


def pontuar_afinidade(
    categoria: str | None,
    interesses: Iterable[str],
    metrica: str = "cosseno",
    peso_cosseno: float = 0.7,
) -> float:
    if metrica not in {"cosseno", "hibrido"}:
        raise ValueError("Métrica de recomendação inválida.")
    pontuacao = decompor_afinidade(categoria, interesses, peso_cosseno)
    return pontuacao.cosseno if metrica == "cosseno" else pontuacao.hibrido


def rankear_pontos(
    pontos: Iterable[PontoRanqueavel],
    interesses: Iterable[str],
    metrica: str = "cosseno",
    peso_cosseno: float = 0.7,
) -> list[PontoPontuado]:
    interesses_materializados = tuple(interesses)
    ranking = [
        PontoPontuado(
            ponto=ponto,
            afinidade=pontuar_afinidade(
                ponto.categoria,
                interesses_materializados,
                metrica,
                peso_cosseno,
            ),
        )
        for ponto in pontos
    ]
    ranking.sort(
        key=lambda item: (
            -item.afinidade,
            -(item.ponto.avaliacao_media or 0.0),
            item.ponto.nome.casefold(),
        )
    )
    return ranking
