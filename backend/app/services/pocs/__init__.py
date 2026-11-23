"""Serviços derivados das provas de conceito de recomendação e roteirização."""

from .matriz_deslocamentos import MatrizDeslocamentos, obter_matriz_deslocamentos
from .otimizacao import RotaInviavelError, otimizar_rota
from .recomendacao import decompor_afinidade, pontuar_afinidade, rankear_pontos

__all__ = [
    "MatrizDeslocamentos",
    "RotaInviavelError",
    "decompor_afinidade",
    "obter_matriz_deslocamentos",
    "otimizar_rota",
    "pontuar_afinidade",
    "rankear_pontos",
]
