                                                                                                   
from __future__ import annotations
import argparse, csv
from pathlib import Path
from nextrip_base import BASE,carregar_pontos,avaliar_rota,validar_rota,salvar_json
from poc1_recomendacao import calcular_afinidades
from solvers import multiobjetivo_ortools,pontuacao_rota
from providers import obter_matriz

def executar(pontos, matriz, catalogo_arquivo, perfil_arquivo, paradas=4, limite=480,
             pesos=(0., .5, .8, 1.), referencia=240, segundos=10):
    from nextrip_arquitetura.servicos import RoteiroService
    return RoteiroService().gerar_roteiro_otimizado(
        pontos, matriz, catalogo_arquivo, perfil_arquivo, paradas, limite, pesos,
        referencia, segundos, solver=multiobjetivo_ortools,
        pontuador=pontuacao_rota, afinidades=calcular_afinidades
    )


def exportar_csv(caminho,resultado):
    p=Path(caminho);p.parent.mkdir(parents=True,exist_ok=True)
    colunas=['alpha_preferencias','afinidade_media_cosseno','deslocamento_min','visitas_min','total_min','score_objetivo','atracoes']
    with p.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=colunas,delimiter=';');w.writeheader()
        for r in resultado['resultados']:
            w.writerow({**{k:r[k] for k in colunas if k!='atracoes'},
                        'atracoes':' | '.join(x['nome'] for x in r['atracoes'])})

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--catalogo',default=str(BASE/'dados'/'catalogo.json'))
    ap.add_argument('--perfil',default=str(BASE/'dados'/'perfil_usuario.json'))
    ap.add_argument('--provedor',choices=('osrm','google'),default='osrm')
    ap.add_argument('--autorizar-google',action='store_true')
    ap.add_argument('--paradas',type=int,default=4)
    ap.add_argument('--limite',type=int,default=480)
    ap.add_argument('--referencia',type=int,default=240)
    ap.add_argument('--pesos',default='0,0.5,0.8,1')
    ap.add_argument('--segundos',type=int,default=10)
    a=ap.parse_args()
    _,pontos=carregar_pontos(a.catalogo)
    mat=obter_matriz(pontos,a.provedor,a.autorizar_google)
    pesos=[float(t) for t in a.pesos.split(',')]
    r=executar(pontos,mat,a.catalogo,a.perfil,a.paradas,a.limite,pesos,a.referencia,a.segundos)
    r['provedor_matriz']=a.provedor
    print('\n=== POC 3 / OR-TOOLS ===')
    for t in r['resultados']:
        print('alpha=',t['alpha_preferencias'],'| afinidade=',t['afinidade_media_cosseno'],
              '| deslocamento=',t['deslocamento_min'],'min | total=',t['total_min'],'min | score=',t['score_objetivo'])
        print(' -> '.join(t['sequencia']))
    if a.provedor=='osrm':
        salvar_json(BASE/'resultados'/'poc3_resultados.json',r)
        exportar_csv(BASE/'resultados'/'poc3_resumo.csv',r)
        print('Resultados: pasta resultados/')
    else:print('Google: resultados não persistidos por precaução com a licença.')

if __name__=='__main__':main()
