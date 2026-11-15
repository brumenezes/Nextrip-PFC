from __future__ import annotations
import argparse
from nextrip_base import BASE, salvar_json
from nextrip_arquitetura.servicos import RecomendacaoIA


def _vetor(v, dimensoes):
    return RecomendacaoIA.validar_vetor(v, dimensoes)


def carregar_entradas(catalogo_arquivo, perfil_arquivo):
    return RecomendacaoIA().carregar_entradas(catalogo_arquivo, perfil_arquivo)


def decompor_pontuacao(usuario, local, dimensoes, peso_cosseno=0.7):
    return RecomendacaoIA().decompor_pontuacao(usuario, local, dimensoes, peso_cosseno)


def calcular_afinidades(catalogo_arquivo, perfil_arquivo, metrica='cosseno', peso_cosseno=0.7):
    return RecomendacaoIA().buscar_similares(catalogo_arquivo, perfil_arquivo, metrica, peso_cosseno)


def executar(catalogo_arquivo, perfil_arquivo, metrica='cosseno', peso_cosseno=0.7):
    return RecomendacaoIA().gerar_ranking(catalogo_arquivo, perfil_arquivo, metrica, peso_cosseno)


def cli(metrica):
    ap=argparse.ArgumentParser()
    ap.add_argument('--catalogo','--locais',dest='catalogo',default=str(BASE/'dados'/'catalogo.json'))
    ap.add_argument('--perfil',default=str(BASE/'dados'/'perfil_usuario.json'))
    ap.add_argument('--top',type=int,default=10)
    ap.add_argument('--peso-cosseno',type=float,default=.7)
    ap.add_argument('--detalhado',action='store_true')
    ap.add_argument('--saida',default=str(BASE/'resultados'/f'poc1_{metrica}.json'))
    args=ap.parse_args()
    dados=executar(args.catalogo,args.perfil,metrica,args.peso_cosseno)
    salvar_json(args.saida,dados)
    print(f'\nPOC 1 - {metrica.upper()} | {dados["origem_catalogo"].get("fonte", "não declarada")}')
    for p in dados['ranking'][:args.top if args.top>0 else None]:
        print(f'{p["score"]:.4f} | {p["nome"]} | {p["id"]}')
        if args.detalhado:print('    ',p['detalhes'])
    print('Evidência:',args.saida)
