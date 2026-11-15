import json, unittest, tempfile
from pathlib import Path
from unittest.mock import patch

from nextrip_base import BASE, carregar_pontos, salvar_json, avaliar_rota, validar_rota
from poc1_recomendacao import calcular_afinidades, executar as executar_poc1
from providers import converter_elementos_overpass, matriz_osrm, matriz_google, _segundos_para_minutos
from solvers import verificar_ortools

class Resposta:
    def __init__(self,payload):self.payload=payload
    def raise_for_status(self):pass
    def json(self):return self.payload

class Sessao:
    def __init__(self,payload):self.payload=payload;self.chamadas=0
    def get(self,*a,**k):self.chamadas+=1;return Resposta(self.payload)
    def post(self,*a,**k):self.chamadas+=1;return Resposta(self.payload)

class TestsNexTrip(unittest.TestCase):
    def setUp(self):
        self.catalogo=BASE/'dados'/'catalogo.json'
        self.perfil=BASE/'dados'/'perfil_usuario.json'
        _,self.pontos=carregar_pontos(self.catalogo)
        self.n=len(self.pontos)
                                                                                         
        self.matriz=[[0 if i==j else 8+abs(i-j)*3 for j in range(self.n)] for i in range(self.n)]

    def test_poc1_scores(self):
        scores=calcular_afinidades(self.catalogo,self.perfil)
        self.assertEqual(len(scores),self.n-1)
        self.assertTrue(all(0<=v<=1 for v in scores.values()))

    def test_poc1_ranking(self):
        x=executar_poc1(self.catalogo,self.perfil,'cosseno')
        self.assertEqual([r['score'] for r in x['ranking']],sorted([r['score'] for r in x['ranking']],reverse=True))

    def test_hibrido_nao_e_igual_cosseno_necessariamente(self):
        a=calcular_afinidades(self.catalogo,self.perfil)
        b=calcular_afinidades(self.catalogo,self.perfil,metrica='hibrido')
        self.assertTrue(any(abs(a[k]-b[k])>1e-5 for k in a))

    def test_validar_ids(self):
        validar_rota([0,1,2,0],2,self.n)
        with self.assertRaises(ValueError):validar_rota([0,1,1,0],2,self.n)

    def test_osrm_mock(self):
        payload={'code':'Ok','durations':[[0,123],[61,0]],'distances':[[0,1000],[800,0]]}
        mat=matriz_osrm(self.pontos[:2],Sessao(payload))
        self.assertEqual(mat,[[0,3],[2,0]])

    def test_osrm_sem_rota_falha_explicitamente(self):
        with self.assertRaises(ValueError):_segundos_para_minutos([[0,None],[30,0]],2)

    def test_google_inativo_nao_chama_api(self):
        s=Sessao([])
        with self.assertRaises(PermissionError):matriz_google(self.pontos[:2],False,s)
        self.assertEqual(s.chamadas,0)

    def test_google_mock(self):
        rows=[]
        for i in range(2):
            for j in range(2):
                rows.append({'originIndex':i,'destinationIndex':j,'condition':'ROUTE_EXISTS','status':{},
                             'duration':f'{(i+j+1)*60}s'})
        with patch.dict('os.environ',{'GOOGLE_MAPS_API_KEY':'chave-ficticia'}):
            mat=matriz_google(self.pontos[:2],True,Sessao(rows))
        self.assertEqual(mat,[[0,2],[2,0]])

    def test_orquestracao_offline_com_roteiros_mockados(self):
                                                                       
        from executar_todas import executar
        rota=[0,1,2,3,0]
        with patch('poc2_otimizacao.tsp_ortools',return_value=rota), \
             patch('poc3_personalizacao_rota.multiobjetivo_ortools',return_value=rota):
            resultado=executar(self.catalogo,self.perfil,self.matriz,
                              quantidade=3,paradas=3,limite=480,pesos=[0,.5],segundos=1)
        self.assertTrue(resultado['integracao']['ok'])
        self.assertEqual(resultado['integracao']['afinidades_conferidas'],6)

    def test_osm_parse(self):
        dados=[{'type':'node','id':123,'lat':-23.5,'lon':-46.6,
                'tags':{'name':'Museu de Teste','tourism':'museum'}},
               {'type':'way','id':999,'center':{'lat':-23.6,'lon':-46.7},
                'tags':{'name':'Parque de Teste','leisure':'park'}}]
        pts=converter_elementos_overpass(dados,5)
        self.assertEqual(len(pts),2)
        self.assertTrue(pts[0]['id'].startswith('osm:'))
        self.assertTrue(all('vetor' in p for p in pts))

class TestIntegracaoComORtools(TestsNexTrip):
    @classmethod
    def setUpClass(cls):
        try:verificar_ortools()
        except RuntimeError:raise unittest.SkipTest('OR-Tools não instalado neste ambiente; necessário para integração.')

    def test_poc2_or_tools(self):
        from poc2_otimizacao import executar
        d=executar(self.pontos,self.matriz,4,1)
        self.assertEqual(len(d['otimizada']['indices']),6)
        self.assertLessEqual(d['otimizada']['deslocamento_min'],d['referencia']['deslocamento_min'])

    def test_poc3_or_tools(self):
        from poc3_personalizacao_rota import executar
        d=executar(self.pontos,self.matriz,self.catalogo,self.perfil,3,360,[0.0,.5,1.0],240,1)
        self.assertEqual(len(d['resultados']),3)
        self.assertTrue(all(r['total_min']<=360 for r in d['resultados']))

    def test_integracao_or_tools(self):
        from executar_todas import executar
        d=executar(self.catalogo,self.perfil,self.matriz,4,3,360,[0.0,.5],240,1)
        self.assertTrue(d['integracao']['ok'])
        self.assertEqual(d['integracao']['afinidades_conferidas'],6)

if __name__=='__main__':unittest.main()
