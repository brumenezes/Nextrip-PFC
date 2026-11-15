                                                                                          
from __future__ import annotations
import math, os, re
import requests
from nextrip_base import DIMENSOES, validar_matriz

                                                                      
                                                                      
                                                     
OVERPASS_URLS = (
    'https://overpass.private.coffee/api/interpreter',
    'https://lz4.overpass-api.de/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
)
OVERPASS_URL = OVERPASS_URLS[0]                               

OSRM_URL = 'https://router.project-osrm.org'
GOOGLE_URL = 'https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix'

                                                                                          
PERFIS_CATEGORIA = {
 'museu':     [1,.85,.05,.05,.05,.05],
 'galeria':   [1,.35,.10,.05,.10,.10],
 'cultura':   [1,.45,.10,.05,.05,.15],
 'historia':  [.80,1,.05,.05,.05,.05],
 'parque':    [.20,.10,.05,1,.05,.05],
 'mirante':   [.30,.10,.05,.85,.05,.05],
 'atracao':   [.65,.45,.15,.35,.15,.10],
 'compras':   [.10,.05,.40,.05,1,.20],
 'gastronomia':[.15,.10,1,.05,.30,.20],
}

def categoria_osm(tags):
    tourism=tags.get('tourism','')
    leisure=tags.get('leisure','')
    if tourism=='museum': return 'museu'
    if tourism=='gallery': return 'galeria'
    if tourism=='viewpoint': return 'mirante'
    if tourism in ('attraction','zoo','aquarium'): return 'atracao'
    if leisure in ('park','garden'): return 'parque'
    if tags.get('historic') in ('monument','memorial','archaeological_site','castle'): return 'historia'
    if tags.get('amenity') in ('arts_centre','theatre'): return 'cultura'
    return None

def vetor_categoria(cat):
    return dict(zip(DIMENSOES, PERFIS_CATEGORIA[cat]))

def converter_elementos_overpass(elementos, limite=12):
    saida=[]; vistos=set()
    for e in elementos:
        tags=e.get('tags') or {}
        nome=(tags.get('name:pt') or tags.get('name') or '').strip()
        cat=categoria_osm(tags)
        centro=e.get('center') or e
        lat,lon=centro.get('lat'), centro.get('lon')
        ident=f"osm:{e.get('type')}:{e.get('id')}"
        if not nome or cat is None or lat is None or lon is None or ident in vistos:
            continue
        vistos.add(ident)
                                                                         
        duracao=70 if cat in ('museu','galeria') else 50 if cat in ('parque','atracao') else 35
        saida.append({'id':ident,'nome':nome,'categoria':cat,'lat':float(lat),'lon':float(lon),
                     'duracao_min':duracao,'vetor':vetor_categoria(cat),
                     'origem_dado':'OpenStreetMap/Overpass', 'url_osm':f"https://www.openstreetmap.org/{e['type']}/{e['id']}"})
                                                                              
    grupos={}
    for p in saida:
        grupos.setdefault(p['categoria'],[]).append(p)
    for grupo in grupos.values():
        grupo.sort(key=lambda x:(x['nome'].casefold(),x['id']))
    selecionados=[]
    while len(selecionados)<limite and any(grupos.values()):
        for categoria in sorted(grupos):
            if grupos[categoria] and len(selecionados)<limite:
                selecionados.append(grupos[categoria].pop(0))
    return selecionados

def gerar_query_overpass(bbox):
                                                                              
    if len(bbox) != 4 or not (-90 <= bbox[0] < bbox[2] <= 90) or not (-180 <= bbox[1] < bbox[3] <= 180):
        raise ValueError('BBox inválida: informe sul,oeste,norte,leste.')
    bb = ','.join(str(float(x)) for x in bbox)
    return f'''[out:json][timeout:25];
(
  nwr["tourism"="museum"]["name"]({bb});
  nwr["tourism"="attraction"]["name"]({bb});
  nwr["tourism"="gallery"]["name"]({bb});
  nwr["leisure"="park"]["name"]({bb});
);
out center 120;'''


def importar_overpass_json(caminho, limite=12):
                                                                                 
    import json
    from pathlib import Path
    payload=json.loads(Path(caminho).read_text(encoding='utf-8-sig'))
    if not isinstance(payload,dict) or not isinstance(payload.get('elements'),list):
        raise ValueError('Arquivo inválido: exporte os dados brutos do Overpass no formato JSON (campo elements).')
    if payload.get('remark'):
        raise RuntimeError('O arquivo contém um erro do servidor Overpass: '+str(payload['remark']))
    dados=converter_elementos_overpass(payload['elements'],limite)
    if len(dados)<2:
        raise ValueError('O arquivo possui menos de 2 atrações adequadas. Amplie a área da consulta.')
    return dados


def consultar_overpass(bbox, limite=12, sessao=None):
                                                                                   
    if not 2 <= limite <= 40:
        raise ValueError('Use 2 a 40 pontos por coleta.')
    query=gerar_query_overpass(bbox)
    cliente=sessao or requests
    erros=[]
    for endereco in OVERPASS_URLS:
        try:
            print(f'Consultando Overpass: {endereco}', flush=True)
            r=cliente.post(endereco, data={'data':query}, timeout=(10,30),
                headers={'User-Agent':'NexTrip-TCC-POC/1.1 (estudo-academico; contato via README)'})
            r.raise_for_status()
            resposta=r.json()
            if resposta.get('remark'):
                raise RuntimeError(str(resposta['remark']))
            objetos=converter_elementos_overpass(resposta.get('elements',[]),limite)
            if len(objetos)<2:
                raise RuntimeError('Poucas atrações nessa área; experimente uma bbox maior.')
            print(f'Coleta bem-sucedida: {len(objetos)} atrações em {endereco}')
            return objetos
        except (requests.Timeout,requests.ConnectionError,requests.HTTPError,ValueError,RuntimeError) as exc:
                                                                                      
            if isinstance(exc, requests.HTTPError):
                status=getattr(getattr(exc,'response',None),'status_code',None)
                if status is not None and status in (400,401,403,406):
                    raise RuntimeError(f'Overpass rejeitou a consulta (HTTP {status}): {endereco}') from exc
            erros.append(f'{endereco}: {type(exc).__name__} ({str(exc)[:80]})')
            print(f'Falha temporária: {type(exc).__name__}; tentando servidor seguinte.',flush=True)
    raise RuntimeError('Nenhum servidor Overpass respondeu com dados válidos. '
                       'A base anterior não foi alterada. Use a importação de arquivo JSON bruto ou tente mais tarde. '
                       + ' | '.join(erros))

def matriz_osrm(pontos, sessao=None):
                                                                                             
    if len(pontos)>20:
        raise ValueError('Limite conservador da POC: até 20 locais por chamada OSRM.')
    coords=';'.join(f"{p['lon']},{p['lat']}" for p in pontos)
    url=f'{OSRM_URL}/table/v1/driving/{coords}'
    r=(sessao or requests).get(url,params={'annotations':'duration,distance'},timeout=45,
                 headers={'User-Agent':'NexTrip-TCC-POC/1.0 (estudo-academico)'})
    r.raise_for_status()
    payload=r.json()
    if payload.get('code')!='Ok' or not payload.get('durations'):
        raise RuntimeError(f'OSRM não conseguiu calcular a matriz: {payload.get("message",payload.get("code"))}')
    return _segundos_para_minutos(payload['durations'], len(pontos))

def _segundos_para_minutos(duracoes, n):
    if len(duracoes)!=n or any(len(row)!=n for row in duracoes):
        raise ValueError('Matriz HTTP incompleta.')
    matriz=[]
    for i,row in enumerate(duracoes):
        linha=[]
        for j,segundos in enumerate(row):
            if i==j: linha.append(0)
            elif segundos is None or not math.isfinite(float(segundos)) or float(segundos)<0:
                raise ValueError('Há trajetos sem conexão viária na matriz. Reduza a região.')
            else: linha.append(max(1,math.ceil(float(segundos)/60)))
        matriz.append(linha)
    validar_matriz(matriz,n)
    return matriz

def matriz_google(pontos, autorizar=False, sessao=None):
                                                        
    if not autorizar:
        raise PermissionError('Google desativado. Use --autorizar-google e consulte custos/quotas antes.')
    chave=os.environ.get('GOOGLE_MAPS_API_KEY','').strip()
    if not chave:
        raise RuntimeError('Configure GOOGLE_MAPS_API_KEY no ambiente; nunca no código.')
    n=len(pontos)
    if n>10: raise ValueError('Limite prudencial Google nesta POC: máximo 10 locais (100 elementos).')
    def waypoint(p):
        return {'waypoint': {'location': {'latLng':{'latitude':float(p['lat']), 'longitude':float(p['lon'])}}}}
    body={'origins':[waypoint(p) for p in pontos], 'destinations':[waypoint(p) for p in pontos],
          'travelMode':'DRIVE','routingPreference':'TRAFFIC_UNAWARE'}
    headers={'Content-Type':'application/json','X-Goog-Api-Key':chave,
             'X-Goog-FieldMask':'originIndex,destinationIndex,status,condition,distanceMeters,duration'}
    r=(sessao or requests).post(GOOGLE_URL,json=body,headers=headers,timeout=60)
    r.raise_for_status()
    payload=r.json()
    if not isinstance(payload,list): raise RuntimeError('Resposta inesperada da API Google Routes.')
    mat=[[None]*n for _ in range(n)]
    for row in payload:
        i,j=row['originIndex'],row['destinationIndex']
        if not (0<=i<n and 0<=j<n): raise ValueError('Índice inesperado na resposta Google.')
        if i==j: mat[i][j]=0; continue
        if row.get('condition')!='ROUTE_EXISTS' or row.get('status',{}).get('code',0)!=0:
            raise ValueError(f'Google Routes: par sem rota ({i}, {j}): {row.get("status")}')
        seconds=float(re.sub(r's$','',row['duration']))
        mat[i][j]=seconds
                                                                        
    for i in range(n):mat[i][i]=0
    return _segundos_para_minutos(mat,n)

def obter_matriz(pontos, provedor='osrm', autorizar_google=False, sessao=None):
    from nextrip_arquitetura.servicos import IntegracaoExterna
    return IntegracaoExterna().buscar_matriz_distancias(pontos, provedor, autorizar_google, sessao)
