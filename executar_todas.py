from __future__ import annotations
import argparse
from nextrip_base import BASE, carregar_pontos, salvar_json
from poc1_recomendacao import executar as poc1, calcular_afinidades
from poc2_otimizacao import executar as poc2
from poc3_personalizacao_rota import executar as poc3, exportar_csv
from providers import obter_matriz

def executar(catalogo_arquivo, perfil_arquivo, matriz, quantidade=6, paradas=4, limite=480,
             pesos=(0, .5, .8, 1), referencia=240, segundos=10):
    from nextrip_arquitetura.servicos import RoteiroService
    return RoteiroService().executar_pocs(
        catalogo_arquivo, perfil_arquivo, matriz, quantidade, paradas, limite,
        pesos, referencia, segundos, executor_poc1=poc1, executor_poc2=poc2,
        executor_poc3=poc3, calculador_afinidades=calcular_afinidades
    )


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--catalogo',default=str(BASE/'dados'/'catalogo.json'))
    ap.add_argument('--perfil',default=str(BASE/'dados'/'perfil_usuario.json'))
    ap.add_argument('--provedor',choices=('osrm','google'),default='osrm')
    ap.add_argument('--autorizar-google',action='store_true')
    ap.add_argument('--quantidade',type=int,default=6)
    ap.add_argument('--paradas',type=int,default=4)
    ap.add_argument('--limite',type=int,default=480)
    ap.add_argument('--pesos',default='0,0.5,0.8,1')
    ap.add_argument('--referencia',type=int,default=240)
    ap.add_argument('--segundos',type=int,default=10)
    a=ap.parse_args()
    _,pontos=carregar_pontos(a.catalogo)
    matriz=obter_matriz(pontos,a.provedor,a.autorizar_google)
    r=executar(a.catalogo,a.perfil,matriz,a.quantidade,a.paradas,a.limite,
              [float(x) for x in a.pesos.split(',')],a.referencia,a.segundos)
    print('\n=== NEXTRIP: 3 POCs INTEGRADAS COM OR-TOOLS ===')
    print('Dados:', a.catalogo,'| matriz:',a.provedor)
    print('POC 1 - Cosseno TOP 5:')
    for item in r['poc1_cosseno']['ranking'][:5]:print('  ',item['nome'],item['score'])
    print('POC 2 - Deslocamento (ordem cadastrada / otimizada):',
          r['poc2']['referencia']['deslocamento_min'],'/',r['poc2']['otimizada']['deslocamento_min'],'min')
    for c in r['poc3']['resultados']:
        print('POC 3 alpha',c['alpha_preferencias'],'afinidade',c['afinidade_media_cosseno'],
              'deslocamento',c['deslocamento_min'],'min ->',' / '.join(c['sequencia']))
    print('Integração validada:',r['integracao']['afinidades_conferidas'],'afinidades; sem afirmar ótimo global.')
    if a.provedor=='osrm':
        pasta=BASE/'resultados'
        for nome, chave in (('poc1_cosseno.json','poc1_cosseno'),('poc1_hibrido.json','poc1_hibrido'),
                            ('poc2_resultado.json','poc2'),('poc3_resultados.json','poc3'),
                            ('integracao_validada.json','integracao')):
            salvar_json(pasta/nome,r[chave])
        exportar_csv(pasta/'poc3_resumo.csv',r['poc3'])
        print('Arquivos gravados em:',pasta)
    else:print('Google: resultados não persistidos por precaução com a licença.')

if __name__=='__main__':main()
