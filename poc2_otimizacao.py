                                                                                          
from __future__ import annotations
import argparse
from nextrip_base import BASE,carregar_pontos,avaliar_rota,validar_rota, salvar_json
from solvers import tsp_ortools
from providers import obter_matriz

def executar(pontos, matriz, quantidade=6, segundos=5):
    from nextrip_arquitetura.servicos import OtimizadorRotas
    return OtimizadorRotas().calcular_melhor_rota(pontos, matriz, quantidade, segundos, solver=tsp_ortools)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--catalogo',default=str(BASE/'dados'/'catalogo.json'))
    ap.add_argument('--provedor',choices=('osrm','google'),default='osrm')
    ap.add_argument('--autorizar-google',action='store_true')
    ap.add_argument('--quantidade',type=int,default=6)
    ap.add_argument('--segundos',type=int,default=5)
    a=ap.parse_args()
    _,pontos=carregar_pontos(a.catalogo)
    matriz=obter_matriz(pontos,a.provedor,a.autorizar_google)
    r=executar(pontos,matriz,a.quantidade,a.segundos)
    r['provedor_matriz']=a.provedor
    print('\n=== POC 2 / OR-TOOLS ===')
    for k in ('referencia','otimizada'):
        x=r[k];print(k.upper(), ' -> '.join(x['sequencia']), '| Deslocamento:',x['deslocamento_min'],'min')
    print('Redução vs ordem cadastrada:',r['reducao_percentual'],'%')
    if a.provedor=='osrm':salvar_json(BASE/'resultados'/'poc2_resultado.json',r)
    else:print('Google: resultados não persistidos por precaução com a licença.')

if __name__=='__main__':main()
