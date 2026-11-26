from datetime import date, timedelta
from itertools import count

from locust import HttpUser, task, between
from locust.exception import StopUser


QUANTIDADE_USUARIOS = 100
SENHA_TESTE = "NextripPerformance123"

contador_usuarios = count(0)


class UsuarioNexTrip(HttpUser):

    wait_time = between(1, 3)

    def on_start(self):
        """
        Executado quando um usuário virtual é iniciado.
        """

        numero = next(contador_usuarios) % QUANTIDADE_USUARIOS + 1

        self.email = f"performance{numero:03d}@example.com"
        self.senha = SENHA_TESTE
        self.token = None

        if not self.autenticar():
            raise StopUser()

    def autenticar(self):
        """
        Realiza o login e armazena o token JWT.
        """

        with self.client.post(
            "/auth/login",
            json={
                "email": self.email,
                "senha": self.senha,
            },
            name="POST /auth/login",
            catch_response=True,
            timeout=30,
        ) as resposta:

            if resposta.status_code != 200:
                resposta.failure(
                    f"Login retornou HTTP {resposta.status_code}"
                )
                return False

            try:
                token = resposta.json().get("access_token")

                if not token:
                    resposta.failure("Token JWT ausente")
                    return False

                self.token = token
                resposta.success()
                return True

            except (ValueError, AttributeError):
                resposta.failure("Resposta de login inválida")
                return False

    def cabecalhos(self):
        return {
            "Authorization": f"Bearer {self.token}"
        }

    @task(1)
    def realizar_login(self):
        """
        CT-PERF-01: desempenho da autenticação.
        """

        self.autenticar()

    @task(4)
    def listar_atracoes(self):
        """
        CT-PERF-02: desempenho da consulta de atrações.
        """

        with self.client.get(
            "/pontos-interesse",
            name="GET /pontos-interesse",
            catch_response=True,
            timeout=30,
        ) as resposta:

            if resposta.status_code != 200:
                resposta.failure(
                    f"Consulta retornou HTTP {resposta.status_code}"
                )
                return

            try:
                atracoes = resposta.json()

                if not isinstance(atracoes, list) or not atracoes:
                    resposta.failure("Catálogo vazio ou inválido")
                else:
                    resposta.success()

            except ValueError:
                resposta.failure("Resposta de atrações inválida")

    @task(3)
    def gerar_roteiro(self):
        """
        CT-PERF-03: desempenho da geração de roteiros.
        """

        dados = {
            "data_visita": (
                date.today() + timedelta(days=7)
            ).isoformat(),
            "tempo_disponivel_minutos": 480,
            "orcamento_maximo": 200.0,
            "quantidade_paradas": 5,
            "latitude_origem": -23.5504,
            "longitude_origem": -46.6339,
            "peso_preferencias": 0.8,
            "metrica_recomendacao": "cosseno",
            "peso_cosseno": 0.7,
            "usar_matriz_viaria": False,
            "retornar_origem": False,
        }

        with self.client.post(
            "/roteiros/gerar",
            json=dados,
            headers=self.cabecalhos(),
            name="POST /roteiros/gerar",
            catch_response=True,
            timeout=60,
        ) as resposta:

            if resposta.status_code != 201:
                resposta.failure(
                    f"Geração retornou HTTP {resposta.status_code}"
                )
                return

            try:
                roteiro = resposta.json()

                if not roteiro.get("roteiro_id"):
                    resposta.failure("Roteiro sem identificador")

                elif len(roteiro["atividades"]) != 5:
                    resposta.failure("Quantidade de atividades incorreta")

                elif roteiro["custo_total_estimado"] > 200:
                    resposta.failure("Orçamento excedido")

                elif roteiro["tempo_total_roteiro"] > 480:
                    resposta.failure("Tempo disponível excedido")

                else:
                    resposta.success()

            except (ValueError, KeyError, TypeError, AttributeError):
                resposta.failure("Resposta de roteiro inválida")

    @task(2)
    def listar_roteiros(self):
        """
        CT-PERF-04: desempenho da consulta de roteiros.
        """

        with self.client.get(
            "/roteiros",
            headers=self.cabecalhos(),
            name="GET /roteiros",
            catch_response=True,
            timeout=30,
        ) as resposta:

            if resposta.status_code != 200:
                resposta.failure(
                    f"Consulta retornou HTTP {resposta.status_code}"
                )
                return

            try:
                roteiros = resposta.json()

                if not isinstance(roteiros, list):
                    resposta.failure("Lista de roteiros inválida")
                else:
                    resposta.success()

            except ValueError:
                resposta.failure("Resposta de roteiros inválida")
