from __future__ import annotations

import unicodedata


NOMES_GENERICOS = {
    "abertura",
    "acesso",
    "entrada",
    "portao",
    "saida",
    "sem nome",
    "unnamed",
    "yes",
    "no",
}


def _normalizar_nome(nome: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", nome.strip().casefold())
        if not unicodedata.combining(caractere)
    )


def nome_poi_e_util(nome: str) -> bool:
    normalizado = _normalizar_nome(nome)
    return len(normalizado) >= 4 and normalizado not in NOMES_GENERICOS
