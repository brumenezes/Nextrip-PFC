from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET

import requests

BASE = Path(__file__).resolve().parent
DIMENSOES = ("cultura", "historia", "gastronomia", "natureza", "compras", "vida_noturna")
PERFIS = {
    "museu": [1,.85,.05,.05,.05,.05],
    "galeria": [1,.35,.10,.05,.10,.10],
    "cultura": [1,.45,.10,.05,.05,.15],
    "historia": [.80,1,.05,.05,.05,.05],
    "parque": [.20,.10,.05,1,.05,.05],
    "mirante": [.30,.10,.05,.85,.05,.05],
    "atracao": [.65,.45,.15,.35,.15,.10],
    "compras": [.10,.05,.40,.05,1,.20],
    "gastronomia": [.15,.10,1,.05,.30,.20],
}

                                                                                    
                                                                           
CENTROS_SP = [
    (-23.5505, -46.6339, "Sé"),
    (-23.5350, -46.6350, "Luz"),
    (-23.5455, -46.6415, "República"),
    (-23.5615, -46.6558, "Paulista"),
    (-23.5565, -46.6350, "Liberdade"),
    (-23.5860, -46.6575, "Ibirapuera"),
    (-23.5480, -46.6655, "Pacaembu"),
]
CENTRO_CURITIBA = (-25.4284, -49.2733)
BBBIKE_CURITIBA = "https://download.bbbike.org/osm/bbbike/Curitiba/Curitiba.osm.gz"
OSM_MAP = "https://api.openstreetmap.org/api/0.6/map"
USER_AGENT = "NexTrip-POC-TCC/1.0 (academic single-city OSM test)"


def categoria(tags: dict) -> str | None:
    turismo = tags.get("tourism", "")
    if turismo == "museum": return "museu"
    if turismo == "gallery": return "galeria"
    if turismo == "viewpoint": return "mirante"
    if turismo in ("attraction", "zoo", "aquarium", "artwork"): return "atracao"
    if tags.get("leisure") in ("park", "garden"): return "parque"
    if tags.get("historic") in ("monument", "memorial", "archaeological_site", "castle", "fort"): return "historia"
    if tags.get("amenity") in ("arts_centre", "theatre"): return "cultura"
    if tags.get("amenity") in ("marketplace",): return "gastronomia"
    return None


def _open_xml(caminho):
    return gzip.open(caminho, "rb") if str(caminho).lower().endswith(".gz") else open(caminho, "rb")


def _percorrer(stream, tipo, precisa_nos=None):
                                                                       
    ctx = ET.iterparse(stream, events=("start", "end"))
    _, root = next(ctx)
    for evento, elemento in ctx:
        if evento != "end" or elemento.tag not in ("node", "way", "relation"):
            continue
        tipo_el = elemento.tag
        if tipo == "poi":
            if tipo_el in ("node", "way"):
                tags = {c.get("k"): c.get("v") for c in elemento.iter("tag")}
                nome = (tags.get("name:pt") or tags.get("name") or "").strip()
                cat = categoria(tags)
                if nome and cat:
                    ident = f"osm:{tipo_el}:{elemento.get('id')}"
                    if tipo_el == "node":
                        yield {"id": ident, "nome": nome, "categoria": cat,
                               "lat": float(elemento.get("lat")), "lon": float(elemento.get("lon")),
                               "localizacao_tipo": "node"}
                    else:
                        refs = [n.get("ref") for n in elemento.iter("nd")]
                        if refs:
                            yield {"id": ident, "nome": nome, "categoria": cat,
                                   "refs": refs, "localizacao_tipo": "centro_geometrico_way"}
        elif tipo == "nos" and tipo_el == "node" and elemento.get("id") in precisa_nos:
            yield elemento.get("id"), (float(elemento.get("lat")), float(elemento.get("lon")))
        elemento.clear()
        root.clear()


def extrair_pois_osm(caminho):
    with _open_xml(caminho) as f:
        candidatos = list(_percorrer(f, "poi"))
                                                                                       
    refs = {ref for p in candidatos for ref in p.get("refs", [])}
    nos = {}
    if refs:
        with _open_xml(caminho) as f:
            nos = dict(_percorrer(f, "nos", refs))
    final = []
    for p in candidatos:
        if "refs" in p:
            coords = [nos[r] for r in p.pop("refs") if r in nos]
            if not coords:
                continue
            p["lat"] = sum(x[0] for x in coords)/len(coords)
            p["lon"] = sum(x[1] for x in coords)/len(coords)
        final.append(p)
    return final


def _distancia_km(lat1, lon1, lat2, lon2):
    rad = math.pi/180
    x = (lon2 - lon1)*math.cos((lat1+lat2)*rad/2)
    y = lat2-lat1
    return 111.2 * math.hypot(x,y)


def selecionar(pois, limite, origem, raio_km=8):
    grupos = defaultdict(list)
    ids = set()
    for p in pois:
        if p["id"] in ids:
            continue
        ids.add(p["id"])
        if not (-90 <= p['lat'] <= 90 and -180 <= p['lon'] <= 180):
            continue
        dist = _distancia_km(p['lat'], p['lon'], origem[0], origem[1])
        if dist <= raio_km:
            p = dict(p)
            p["distancia_origem_km_aprox"] = round(dist,3)
            grupos[p["categoria"]].append(p)
    for grupo in grupos.values():
        grupo.sort(key=lambda p: (p['distancia_origem_km_aprox'], p['nome'].casefold(),p['id']))
    selecionados = []
    while len(selecionados) < limite and any(grupos.values()):
        for cat in sorted(grupos):
            if grupos[cat] and len(selecionados) < limite:
                p = grupos[cat].pop(0)
                p['vetor'] = dict(zip(DIMENSOES, PERFIS[cat]))
                p['duracao_min'] = (70 if cat in ('museu','galeria') else
                                    50 if cat in ('parque','atracao') else 35)
                p['url_osm'] = 'https://www.openstreetmap.org/' + p['id'].replace('osm:','').replace(':','/')
                p['origem_dado'] = 'OpenStreetMap'
                selecionados.append(p)
    return selecionados


def _salvar_catalogo(destino, pois, cidade, origem, fonte, url_fonte):
    if len(pois) < 2:
        raise RuntimeError("Não foram encontrados pelo menos dois pontos de interesse OSM válidos. Catálogo preservado.")
    catalogo = {
        'dimensoes':list(DIMENSOES),
        'origem': {'id':'origem:usuario','nome':f'Ponto de partida - {cidade}',
                   'lat':origem[0],'lon':origem[1],'duracao_min':0},
        'atracoes':pois,
        'metadados': {
            'fonte':'OpenStreetMap', 'via':fonte, 'url_fonte':url_fonte,
            'cidade':cidade, 'coletado_em_utc':datetime.now(timezone.utc).isoformat(),
            'licenca':'ODbL 1.0', 'atribuicao':'© OpenStreetMap contributors',
            'url_licenca':'https://www.openstreetmap.org/copyright',
            'localizacoes':'obtidas de objetos OSM; way usa média das coordenadas de seus vértices, não entrada',
            'duracoes':'estimativas demonstrativas por categoria; não provenientes do OSM',
            'vetores':'heurísticos por categoria; não são embeddings de IA',
        },
    }
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
                                                                               
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.json',
                                     dir=str(destino.parent), delete=False) as f:
        temp_nome = f.name
        json.dump(catalogo,f,ensure_ascii=False,indent=2)
    try:
        os.replace(temp_nome, destino)
    finally:
        if os.path.exists(temp_nome): os.unlink(temp_nome)
    return catalogo


def _baixar(destino, url, tempo=70):
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + '.part')
    with requests.get(url, timeout=(10, tempo), stream=True,
                      headers={'User-Agent': USER_AGENT}) as resposta:
        resposta.raise_for_status()
        with temporario.open('wb') as f:
            total = 0
            for chunk in resposta.iter_content(65536):
                if chunk:
                    total += len(chunk)
                    if total > 100_000_000:
                        raise RuntimeError('Arquivo inesperadamente grande (>100MB).')
                    f.write(chunk)
    os.replace(temporario, caminho)
    return caminho


def _extrair_sp_api(limite):
                                                                    
                                                                    
    candidatos = []
    erros = []
    falhas_seguidas = 0
    with tempfile.TemporaryDirectory(prefix='nextrip_osm_') as pasta:
        for i,(lat,lon,bairro) in enumerate(CENTROS_SP,1):
            bbox = f'{lon-.0035:.6f},{lat-.0025:.6f},{lon+.0035:.6f},{lat+.0025:.6f}'
            print(f'  [{i}/{len(CENTROS_SP)}] API OSM: {bairro} | bbox={bbox}',flush=True)
            try:
                arquivo = Path(pasta)/f'osm_{i}.osm'
                _baixar(arquivo, OSM_MAP+'?bbox='+bbox,tempo=18)
                pontos = extrair_pois_osm(arquivo)
                print(f'      {len(pontos)} POIs nomeados/categorizados encontrados')
                candidatos.extend(pontos)
                falhas_seguidas = 0
                resultado = selecionar(candidatos,limite,(-23.5504,-46.6339))
                if len(resultado) >= limite:
                    return resultado
            except (requests.RequestException, OSError, ET.ParseError, ValueError, RuntimeError) as exc:
                falhas_seguidas += 1
                erros.append(f'{bairro}: {type(exc).__name__}: {str(exc)[:100]}')
                print(f'      Falha: {type(exc).__name__}: {str(exc)[:120]}',flush=True)
                if falhas_seguidas >= 2:
                    print('  API principal indisponível em 2 regiões consecutivas. Interrompendo tentativas.',flush=True)
                    break
            time.sleep(1.0)                               
    resultado = selecionar(candidatos,limite,(-23.5504,-46.6339))
    if len(resultado)>=2:
        return resultado
    raise RuntimeError('API OSM de São Paulo sem dados suficientes. '+ ' | '.join(erros))


def _extrair_curitiba_bbbike(limite, arquivo=None):
    destino = Path(arquivo) if arquivo else BASE/'dados'/'Curitiba.osm.gz'
    if not destino.is_file():
        print('Baixando extrato OSM pronto do BBBike para Curitiba (17 MB aprox.)...', flush=True)
        try:
            _baixar(destino, BBBIKE_CURITIBA, tempo=110)
        except Exception:
            destino.with_suffix(destino.suffix+'.part').unlink(missing_ok=True)
            raise
    else:
        print(f'Usando extrato OSM local: {destino}',flush=True)
    pois = extrair_pois_osm(destino)
    print(f'{len(pois)} objetos OSM turísticos nomeados no extrato; selecionando os mais próximos do centro.')
    return selecionar(pois, limite, CENTRO_CURITIBA, raio_km=12)


def executar(fonte='auto', limite=12, saida=None, arquivo_osm=None):
    if not 2 <= limite <= 30:
        raise ValueError('--limite deve estar entre 2 e 30')
    saida = Path(saida) if saida else BASE/'dados'/'catalogo.json'
    if arquivo_osm:
        caminho = Path(arquivo_osm)
        if not caminho.exists(): raise FileNotFoundError(caminho)
        cidade='Curitiba' if 'curitiba' in caminho.name.casefold() else 'São Paulo (verifique a origem do arquivo)'
        origem = CENTRO_CURITIBA if cidade=='Curitiba' else (-23.5504,-46.6339)
        selecionados = selecionar(extrair_pois_osm(caminho),limite,origem,raio_km=12)
        via='Arquivo OSM XML local'
        url=str(caminho)
    elif fonte in ('sp','auto'):
        try:
            selecionados = _extrair_sp_api(limite)
            cidade='São Paulo'; origem=(-23.5504,-46.6339)
            via='API principal OSM /api/0.6/map'; url=OSM_MAP
        except Exception as exc:
            if fonte == 'sp': raise
            print('\nAVISO: API de São Paulo indisponível:', exc,flush=True)
            print('ALTERNATIVA EXPLÍCITA: tentando extrato real OSM de CURITIBA via BBBike.',flush=True)
            selecionados=_extrair_curitiba_bbbike(limite)
            cidade='Curitiba';origem=CENTRO_CURITIBA
            via='Extrato pré-processado BBBike OSM'; url=BBBIKE_CURITIBA
    elif fonte=='curitiba':
        selecionados=_extrair_curitiba_bbbike(limite)
        cidade='Curitiba';origem=CENTRO_CURITIBA
        via='Extrato pré-processado BBBike OSM'; url=BBBIKE_CURITIBA
    else:
        raise ValueError('Escolha --fonte auto, sp ou curitiba')
    resultado=_salvar_catalogo(saida,selecionados,cidade,origem,via,url)
    print(f'\nSUCESSO: {len(selecionados)} atrações OSM de {cidade} salvas em {saida}',flush=True)
    print(f'FONTE: {via}\n',flush=True)
    for p in resultado['atracoes']:
        print(f"{p['id']:<24} | {p['nome']:<42} | {p['categoria']:<10} | {p['lat']:.6f}, {p['lon']:.6f}")
    return resultado


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonte',choices=['auto','sp','curitiba'],default='auto',
                        help='auto: tenta São Paulo; se falhar, baixa extrato real de Curitiba (avisado).')
    parser.add_argument('--limite',type=int,default=12)
    parser.add_argument('--saida',default=str(BASE/'dados'/'catalogo.json'))
    parser.add_argument('--arquivo-osm',default=None,
                        help='Importa arquivo .osm/.osm.gz que você já baixou. Sem chamadas HTTP.')
    a=parser.parse_args()
    try:
        executar(fonte=a.fonte,limite=a.limite,saida=a.saida,arquivo_osm=a.arquivo_osm)
    except Exception as exc:
        print('\nFALHA NA COLETA:', type(exc).__name__, exc,flush=True)
        print('Nenhum catálogo antigo foi substituído. Consulte README.md para importar extrato pelo navegador.')
        raise SystemExit(1)


if __name__=='__main__':
    main()
