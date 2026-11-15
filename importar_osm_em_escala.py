from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
import gzip
import json
import math
import os
from pathlib import Path
import re
import tempfile
import unicodedata
import xml.etree.ElementTree as ET

DIMENSOES = ("cultura", "historia", "gastronomia", "natureza", "compras", "vida_noturna")
PERFIS = {
    "museu": [1, .85, .05, .05, .05, .05],
    "galeria": [1, .35, .10, .05, .10, .10],
    "cultura": [1, .45, .10, .05, .05, .15],
    "historia": [.80, 1, .05, .05, .05, .05],
    "parque": [.20, .10, .05, 1, .05, .05],
    "mirante": [.30, .10, .05, .85, .05, .05],
    "atracao": [.65, .45, .15, .35, .15, .10],
    "compras": [.10, .05, .40, .05, 1, .20],
    "gastronomia": [.15, .10, 1, .05, .30, .20],
    "vida_noturna": [.20, .05, .35, .05, .20, 1],
}
CATEGORIAS_PADRAO = ("museu", "galeria", "cultura", "historia", "parque", "mirante", "atracao")
TAGS_UTEIS = ("tourism", "historic", "leisure", "amenity", "shop", "building", "office", "access", "opening_hours", "website", "wikidata", "wikipedia")


def categorizar(tags: dict) -> str | None:
    turismo = tags.get("tourism")
    if turismo == "museum": return "museu"
    if turismo == "gallery": return "galeria"
    if turismo == "viewpoint": return "mirante"
    if turismo in ("attraction", "zoo", "aquarium", "artwork", "theme_park"): return "atracao"
    if tags.get("leisure") in ("park", "garden", "nature_reserve"): return "parque"
    if tags.get("historic") in ("monument", "memorial", "archaeological_site", "castle", "fort", "ruins", "wayside_shrine"): return "historia"
    if tags.get("amenity") in ("arts_centre", "theatre"): return "cultura"
    if tags.get("amenity") in ("restaurant", "cafe", "marketplace", "food_court"): return "gastronomia"
    if tags.get("amenity") in ("pub", "bar", "nightclub"): return "vida_noturna"
    if tags.get("shop") in ("mall", "department_store"): return "compras"
    return None


def distancia_km(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    rad = math.pi / 180
    return 111.2 * math.hypot((lon2-lon1)*math.cos((lat1+lat2)*rad/2), lat2-lat1)


def _arquivo(path):
    return gzip.open(path, "rb") if str(path).lower().endswith(".gz") else open(path, "rb")


def _normalizar_nome(nome):
    nfkd = unicodedata.normalize("NFKD", nome)
    simples = "".join(c for c in nfkd if not unicodedata.combining(c)).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", simples))


def _percorrer(path, modo, refs=None):
    with _arquivo(path) as stream:
        context = ET.iterparse(stream, events=("start", "end"))
        _, root = next(context)
        for evento, item in context:
            if evento != "end" or item.tag not in ("node", "way", "relation"):
                continue
            tipo = item.tag
            if modo == "coletar" and tipo in ("node", "way"):
                tags = {e.get("k"): e.get("v") for e in item.iter("tag")}
                nome = (tags.get("name:pt") or tags.get("name") or "").strip()
                cat = categorizar(tags)
                                                                                                           
                if nome and cat and tags.get("access") not in ("private", "no") and tags.get("disused") != "yes" \
                    and tags.get("abandoned") != "yes" and tags.get("office") != "government" \
                    and tags.get("amenity") not in ("school", "college", "university"):
                    dado = {"id": f"osm:{tipo}:{item.get('id')}", "nome": nome,
                            "categoria": cat, "tags_osm": {k: tags[k] for k in TAGS_UTEIS if k in tags}}
                    if tipo == "node":
                        try:
                            dado["lat"], dado["lon"] = float(item.get("lat")), float(item.get("lon"))
                            yield dado
                        except (TypeError, ValueError):
                            pass
                    else:
                        dado["refs"] = [e.get("ref") for e in item.iter("nd") if e.get("ref")]
                        if dado["refs"]:
                            yield dado
            if modo == "refs" and tipo == "node" and item.get("id") in refs:
                try:
                    yield item.get("id"), (float(item.get("lat")), float(item.get("lon")))
                except (TypeError, ValueError):
                    pass
            item.clear()
            root.clear()


def ler_osm(path):
    dados = list(_percorrer(path, "coletar"))
    referencias = {ref for item in dados for ref in item.get("refs", ())}
    nodos = dict(_percorrer(path, "refs", referencias)) if referencias else {}
    final = []
    for item in dados:
        if "refs" in item:
            coords = [nodos[r] for r in item.pop("refs") if r in nodos]
            if not coords:
                continue
                                                                                                         
            item["lat"] = sum(x for x, _ in coords) / len(coords)
            item["lon"] = sum(y for _, y in coords) / len(coords)
            item["tipo_coordenada"] = "media_vertices_way"
        else:
            item["tipo_coordenada"] = "node_osm"
        final.append(item)
    return final


def preparar(pois, origem, categorias, raio, limite, dedup_metros, exclusoes, celula_km=1.2):
    disponiveis = []
    for poi in pois:
        if poi["categoria"] not in categorias or any(x in _normalizar_nome(poi["nome"]) for x in exclusoes):
            continue
        lat, lon = poi["lat"], poi["lon"]
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        d = distancia_km((lat, lon), origem)
        if d > raio:
            continue
        p = dict(poi)
        p["distancia_origem_km_aprox"] = round(d, 3)
        p["vetor"] = dict(zip(DIMENSOES, PERFIS[p["categoria"]]))
        p["duracao_min"] = 70 if p["categoria"] in ("museu", "galeria") else (50 if p["categoria"] in ("atracao", "parque") else 35)
        p["url_osm"] = "https://www.openstreetmap.org/" + p["id"].replace("osm:", "").replace(":", "/")
        p["origem_dado"] = "OpenStreetMap"
        disponiveis.append(p)

                                                                               
    disponiveis.sort(key=lambda p: (-len(p["tags_osm"]), p["distancia_origem_km_aprox"], p["id"]))
    vistos_id = set()
    vistos_nome = defaultdict(list)
    unicos = []
    for p in disponiveis:
        if p["id"] in vistos_id:
            continue
        chave = _normalizar_nome(p["nome"])
        if any(distancia_km((p["lat"], p["lon"]), xy) * 1000 < dedup_metros for xy in vistos_nome[chave]):
            continue
        vistos_id.add(p["id"])
        vistos_nome[chave].append((p["lat"], p["lon"]))
        unicos.append(p)

                                                                                       
    grupos = defaultdict(lambda: defaultdict(list))
    for p in unicos:
        x = math.floor((p["lat"] - origem[0]) * 111.2 / celula_km)
        y = math.floor((p["lon"] - origem[1]) * 111.2 * math.cos(math.radians(origem[0])) / celula_km)
        grupos[p["categoria"]][(x, y)].append(p)
    por_categoria = {}
    for cat in sorted(grupos):
        tiles = sorted(grupos[cat], key=lambda t: (abs(t[0])+abs(t[1]), t))
        filas = deque(deque(sorted(grupos[cat][tile], key=lambda x: x["nome"].casefold())) for tile in tiles)
        ordenados = []
        while filas:
            fila = filas.popleft()
            ordenados.append(fila.popleft())
            if fila:
                filas.append(fila)
        por_categoria[cat] = deque(ordenados)

    final = []
    while len(final) < limite and any(por_categoria.values()):
        for cat in sorted(por_categoria):
            if por_categoria[cat] and len(final) < limite:
                final.append(por_categoria[cat].popleft())
    return final, len(disponiveis), len(unicos)


def gravar(path, atracoes, origem, cidade, fonte, detalhe):
    if len(atracoes) < 2:
        raise ValueError("Menos de 2 atrações válidas. Amplie o raio ou as categorias.")
    dados = {
        "dimensoes": list(DIMENSOES),
        "origem": {"id":"origem:usuario", "nome":f"Ponto de partida - {cidade}",
                   "lat":origem[0],"lon":origem[1],"duracao_min":0},
        "atracoes":atracoes,
        "metadados":{"fonte":"OpenStreetMap","via":fonte,"cidade":cidade,
                     "arquivo_origem":detalhe,"processado_em_utc":datetime.now(timezone.utc).isoformat(),
                     "licenca":"ODbL 1.0","atribuicao":"© OpenStreetMap contributors",
                     "vetores":"heurísticos por categoria; não são embeddings treinados",
                     "duracoes":"estimativas heurísticas por categoria; não são tempos verificados",
                     "localizacao_way":"média de vértices, pode não coincidir com a entrada"},
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as f:
        temporario = Path(f.name)
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(temporario, path)
    return dados


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arquivo-osm", required=True, help="Extrato BBBike .osm ou .osm.gz")
    p.add_argument("--limite", type=int, default=300, help="Máximo de POIs no catálogo amplo (padrão 300)")
    p.add_argument("--categorias", default=",".join(CATEGORIAS_PADRAO), help="Ex.: museu,galeria,parque,historia,atracao")
    p.add_argument("--origem-lat", type=float, default=-23.5504)
    p.add_argument("--origem-lon", type=float, default=-46.6339)
    p.add_argument("--cidade", default="São Paulo")
    p.add_argument("--raio-km", type=float, default=15)
    p.add_argument("--duplicidade-metros", type=float, default=150)
    p.add_argument("--excluir-nomes", default="", help="Termos separados por vírgula")
    p.add_argument("--subconjunto", type=int, default=15, help="Atrações no catálogo pequeno para OSRM; 2 a 19")
    p.add_argument("--saida-ampla", default="dados/catalogo_amplo.json")
    p.add_argument("--saida-teste", default="dados/catalogo_teste.json")
    args = p.parse_args()
    arquivo = Path(args.arquivo_osm)
    if not arquivo.is_file() or not (str(arquivo).endswith('.osm') or str(arquivo).endswith('.osm.gz')):
        p.error("Forneça arquivo .osm ou .osm.gz existente, extraído do OSM/BBBike.")
    categorias = [c.strip().casefold() for c in args.categorias.split(',') if c.strip()]
    if any(c not in PERFIS for c in categorias):
        p.error(f"Categorias inválidas. Use: {', '.join(PERFIS)}")
    if not (2 <= args.limite <= 10000 and 2 <= args.subconjunto <= 19 and args.subconjunto <= args.limite):
        p.error("Use --limite de 2 a 10000 e --subconjunto de 2 a 19, sem superar limite.")
    if not (0 < args.raio_km <= 200 and 0 <= args.duplicidade_metros <= 1000):
        p.error("Raio ou distância de duplicidade inválida.")
    origem = (args.origem_lat, args.origem_lon)
    if not (-90 <= origem[0] <= 90 and -180 <= origem[1] <= 180):
        p.error("Coordenadas da origem inválidas.")
    exclusoes = [_normalizar_nome(t) for t in args.excluir_nomes.split(',') if t.strip()]
    if Path(args.saida_ampla).resolve() == Path(args.saida_teste).resolve():
        p.error("As saídas devem ser arquivos diferentes.")
    print("Lendo extrato OSM (arquivo local, sem Overpass)...",flush=True)
    brutos = ler_osm(arquivo)
    finais, dentro, unicos = preparar(brutos, origem, set(categorias), args.raio_km,
                                     args.limite, args.duplicidade_metros, exclusoes)
    print(f"POIs com categoria encontrados no extrato: {len(brutos)}")
    print(f"POIs dentro do raio e filtros: {dentro}; após deduplicação: {unicos}")
    print(f"POIs selecionados: {len(finais)}")
    if len(finais) < 2:
        raise SystemExit("Nenhuma saída foi sobrescrita: menos de 2 POIs aptos.")
    subset = finais[:args.subconjunto]
    gravar(args.saida_ampla, finais, origem, args.cidade, "Extrato OSM XML local / BBBike", str(arquivo))
    gravar(args.saida_teste, subset, origem, args.cidade, "Subconjunto do extrato OSM para OSRM", str(arquivo))
    print("Categorias:", dict(Counter(p['categoria'] for p in finais)))
    print("Catálogo amplo:", args.saida_ampla)
    print("Catálogo de teste:", args.saida_teste, f"({len(subset)} atrações + origem)")
    print("AVISO: candidatos OSM reais; duração e vetores são heurísticos e exigem validação.")


if __name__ == "__main__":
    main()
