from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.domain_models import PontoDeInteresse


@dataclass(frozen=True)
class AtracaoOSM:
    identificador: str
    osm_id: int
    nome: str
    categoria: str
    latitude: float
    longitude: float
    duracao_minutos: int
    preco_estimado: float
    dados_brutos: dict[str, Any]


def transformar_atracao(item: dict[str, Any], preco_padrao: float) -> AtracaoOSM:
    identificador = str(item.get("id", ""))
    partes = identificador.split(":")
    if len(partes) != 3 or partes[0] != "osm" or partes[1] not in {"node", "way"}:
        raise ValueError(f"Identificador OSM inválido: {identificador!r}")

    nome = str(item.get("nome", "")).strip()
    categoria = str(item.get("categoria", "")).strip().casefold()
    latitude = float(item["lat"])
    longitude = float(item["lon"])
    duracao = int(item["duracao_min"])
    if not nome or not categoria:
        raise ValueError(f"Nome ou categoria ausente em {identificador}")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError(f"Coordenadas inválidas em {identificador}")
    if duracao <= 0 or preco_padrao < 0:
        raise ValueError(f"Duração ou preço inválido em {identificador}")

    return AtracaoOSM(
        identificador=identificador,
        osm_id=int(partes[2]),
        nome=nome,
        categoria=categoria,
        latitude=latitude,
        longitude=longitude,
        duracao_minutos=duracao,
        preco_estimado=preco_padrao,
        dados_brutos={**item, "identificador": identificador},
    )


def carregar_catalogo(caminho: Path, preco_padrao: float = 0.0) -> list[AtracaoOSM]:
    with caminho.open(encoding="utf-8") as arquivo:
        payload = json.load(arquivo)
    metadados = payload.get("metadados", {})
    if metadados.get("fonte") != "OpenStreetMap":
        raise ValueError("O catálogo deve declarar OpenStreetMap como fonte.")
    if "OpenStreetMap contributors" not in metadados.get("atribuicao", ""):
        raise ValueError("O catálogo não contém a atribuição obrigatória do OSM.")
    atracoes = payload.get("atracoes")
    if not isinstance(atracoes, list) or not atracoes:
        raise ValueError("O catálogo não contém atrações.")
    return [transformar_atracao(item, preco_padrao) for item in atracoes]


def importar_catalogo(
    sessao: Session,
    atracoes: list[AtracaoOSM],
) -> tuple[int, int]:
    criados = 0
    atualizados = 0
    for atracao in atracoes:
        existente = sessao.scalar(
            select(PontoDeInteresse).where(
                PontoDeInteresse.dados_brutos_osm["identificador"].astext
                == atracao.identificador
            )
        )
        valores = {
            "osm_id": atracao.osm_id,
            "nome": atracao.nome,
            "categoria": atracao.categoria,
            "localizacao": func.ST_SetSRID(
                func.ST_MakePoint(atracao.longitude, atracao.latitude),
                4326,
            ),
            "preco_estimado": atracao.preco_estimado,
            "duracao_minutos": atracao.duracao_minutos,
            "dados_brutos_osm": atracao.dados_brutos,
        }
        if existente is None:
            sessao.add(PontoDeInteresse(**valores))
            criados += 1
        else:
            for campo, valor in valores.items():
                setattr(existente, campo, valor)
            atualizados += 1
    return criados, atualizados


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Importa de forma idempotente um catálogo OSM das POCs no PostgreSQL."
    )
    parser.add_argument("catalogo", type=Path)
    parser.add_argument("--preco-padrao", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Valida o arquivo sem abrir conexão com o PostgreSQL.",
    )
    argumentos = parser.parse_args()

    atracoes = carregar_catalogo(argumentos.catalogo, argumentos.preco_padrao)
    if argumentos.validate_only:
        print(f"Catálogo válido: {len(atracoes)} pontos OSM.")
        return
    with SessionLocal() as sessao:
        criados, atualizados = importar_catalogo(sessao, atracoes)
        if argumentos.dry_run:
            sessao.rollback()
        else:
            sessao.commit()
    modo = "simulados" if argumentos.dry_run else "persistidos"
    print(f"{len(atracoes)} pontos {modo}: {criados} criados, {atualizados} atualizados.")


if __name__ == "__main__":
    main()
