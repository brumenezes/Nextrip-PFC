import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from nextrip_base import BASE, carregar_pontos
from nextrip_arquitetura import (
    Usuario, Preferencias, Roteiro, RoteiroDia, VisitaAtividade, PontoDeInteresse,
    RepositorioJSON, RecomendacaoIA, OtimizadorRotas, IntegracaoExterna,
    RoteiroService, ReplanejamentoService, OfflineCacheManager,
    MapaInterativoView, AppMobileController,
)
from poc1_recomendacao import executar as poc1
from executar_todas import executar as executar_todas


class TestArquitetura(unittest.TestCase):
    def setUp(self):
        self.catalogo = BASE / 'dados' / 'catalogo.json'
        self.amplo = BASE / 'dados' / 'catalogo_amplo.json'
        self.perfil = BASE / 'dados' / 'perfil_usuario.json'
        _, self.pontos = carregar_pontos(self.catalogo)
        n = len(self.pontos)
        self.matriz = [[0 if i == j else 8 + abs(i-j)*3 for j in range(n)] for i in range(n)]

    def test_catalogo_sao_paulo_preservado(self):
        amplo = RepositorioJSON().carregar_catalogo(self.amplo)
        self.assertGreaterEqual(len(amplo['atracoes']), 2)
        self.assertEqual(amplo['metadados']['fonte'], 'OpenStreetMap')
        self.assertEqual(amplo['metadados']['cidade'], 'São Paulo')
        self.assertTrue(all(str(p['id']).startswith('osm:') for p in amplo['atracoes']))

    def test_poi_roundtrip_preserva_osm(self):
        original = RepositorioJSON().carregar_catalogo(self.catalogo)['atracoes'][0]
        ponto = PontoDeInteresse.de_json(original)
        self.assertEqual(ponto.para_json(), original)
        self.assertGreaterEqual(ponto.calcular_distancia(ponto), 0)

    def test_preferencias_e_usuario(self):
        preferencias = Preferencias()
        preferencias.atualizar_preferencias({'historia': 0.8})
        usuario = Usuario('1', 'Visitante', preferencias=preferencias)
        usuario.atualizar_perfil(nome='Turista')
        self.assertEqual(usuario.nome, 'Turista')
        self.assertEqual(usuario.preferencias.perfil_embedding['historia'], 0.8)
        with self.assertRaises(NotImplementedError):
            usuario.login()

    def test_modelos_roteiro(self):
        dia = RoteiroDia('1', '2026-11-15')
        dia.adicionar_visita(VisitaAtividade('visita-1', 'osm:node:1', 1))
        dia.visitas[0].marcar_como_concluido()
        self.assertEqual(dia.visitas[0].status, 'concluida')
        self.assertIsNone(Roteiro('1', 'usuario', '2026-11-15', '2026-11-15', dias=[dia]).gerar_resumo_financeiro()['custo_total_estimado'])

    def test_afinidade_ampla(self):
        ranking = RecomendacaoIA().gerar_ranking(self.amplo, self.perfil)
        self.assertEqual(len(ranking['ranking']), len(RepositorioJSON().carregar_catalogo(self.amplo)['atracoes']))
        self.assertEqual(ranking['ranking'], sorted(ranking['ranking'], key=lambda p: (-p['score'], p['nome'])))
        self.assertEqual(ranking, poc1(self.amplo, self.perfil))

    def test_poc2_com_solver_injetado(self):
        rota = [0, 1, 2, 3, 0]
        resultado = OtimizadorRotas().calcular_melhor_rota(self.pontos, self.matriz, 3, 1,
                                                            solver=lambda *_: rota)
        self.assertEqual(resultado['poc'], 2)
        self.assertEqual(resultado['otimizada']['indices'], rota)

    def test_poc3_com_solver_injetado(self):
        service = RoteiroService()
        rota = [0, 1, 2, 3, 0]
        resultado = service.gerar_roteiro_otimizado(
            self.pontos, self.matriz, self.catalogo, self.perfil, 3, 360, (0, 0.8), 240, 1,
            solver=lambda *_: rota
        )
        self.assertEqual(len(resultado['resultados']), 2)
        self.assertTrue(all(r['total_min'] <= 360 for r in resultado['resultados']))

    def test_matriz_osrm_continua_usando_servico(self):
        class Resposta:
            def raise_for_status(self):
                return None
            def json(self):
                return {'code': 'Ok', 'durations': [[0, 90], [100, 0]]}
        class Sessao:
            def get(self, *args, **kwargs):
                return Resposta()
        matriz = IntegracaoExterna().buscar_matriz_distancias(self.pontos[:2], sessao=Sessao())
        self.assertEqual(matriz, [[0, 2], [2, 0]])

    def test_cache_e_mapa(self):
        m = MapaInterativoView()
        marcadores = m.renderizar_marcadores(self.pontos[:2])
        self.assertEqual(marcadores[1]['id'], self.pontos[1]['id'])
        self.assertEqual(len(m.desenhar_rota_sequencial([0, 1, 0], self.pontos)), 3)
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'roteiro.json'
            c = OfflineCacheManager()
            c.salvar_roteiro_local({'visitas': marcadores}, arquivo)
            self.assertEqual(c.carregar_roteiro_local(arquivo)['visitas'], marcadores)
            self.assertFalse(c.verificar_sincronizacao()['sincronizacao_remota_implementada'])

    def test_orquestracao_integrada_compatibilidade(self):
        rota = [0, 1, 2, 3, 0]
        with patch('poc2_otimizacao.tsp_ortools', return_value=rota), \
             patch('poc3_personalizacao_rota.multiobjetivo_ortools', return_value=rota):
            resultado = executar_todas(self.catalogo, self.perfil, self.matriz,
                                      quantidade=3, paradas=3, limite=480, pesos=(0, .5), segundos=1)
        self.assertTrue(resultado['integracao']['ok'])
        self.assertEqual(resultado['integracao']['afinidades_conferidas'], 6)

    def test_controlador_e_replanejamento(self):
        c = AppMobileController()
        params = c.coletar_parametros_usuario(self.catalogo, self.perfil)
        self.assertEqual(params['limite'], 480)
        with patch('solvers.multiobjetivo_ortools', return_value=[0, 1, 2, 0]):
            resultado = ReplanejamentoService().recalcular_rota(
                self.catalogo, self.perfil, self.matriz, paradas=2, limite=480, segundos=1
            )
        self.assertEqual(resultado['resultados'][0]['paradas'] if 'paradas' in resultado['resultados'][0] else resultado['paradas'], 2)
        self.assertEqual(len(c.renderizar_roteiro(resultado)), 1)


if __name__ == '__main__':
    unittest.main()
