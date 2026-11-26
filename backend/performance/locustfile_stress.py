
import gevent

from locust import LoadTestShape
from locust import task

from performance.locustfile import (
    UsuarioNexTrip as UsuarioBase,
    contador_usuarios,
    QUANTIDADE_USUARIOS,
    SENHA_TESTE,
)


class UsuarioNexTripStress(UsuarioBase):

    abstract = False

    def on_start(self):
        """
        Inicializa o usuário sem encerrar sua execução
        caso a primeira tentativa de login falhe.
        """

        numero = (
            next(contador_usuarios)
            % QUANTIDADE_USUARIOS
            + 1
        )

        self.email = (
            f"performance{numero:03d}@example.com"
        )

        self.senha = SENHA_TESTE
        self.token = None

        self.autenticar()

    def autenticar(self):
        """
        Autentica o usuário e registra falhas
        de comunicação com maior detalhamento.
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

            if resposta.status_code == 0:
                erro = getattr(resposta, "error", None)

                tipo_erro = (
                    type(erro).__name__
                    if erro is not None
                    else "ErroDesconhecido"
                )

                resposta.failure(
                    f"Falha de comunicação: {tipo_erro}"
                )

                return False

            if resposta.status_code != 200:
                resposta.failure(
                    f"Login retornou HTTP "
                    f"{resposta.status_code}"
                )

                return False

            try:
                token = resposta.json().get(
                    "access_token"
                )

                if not token:
                    resposta.failure("Token JWT ausente")
                    return False

                self.token = token
                resposta.success()

                return True

            except (ValueError, AttributeError):
                resposta.failure(
                    "Resposta de login inválida"
                )

                return False

    def garantir_autenticacao(self):
        """
        Tenta autenticar novamente quando o usuário
        ainda não possui um token.
        """

        if self.token:
            return True

        if self.autenticar():
            return True

        gevent.sleep(3)

        return False

    @task(1)
    def realizar_login(self):
        self.autenticar()

    @task(4)
    def listar_atracoes(self):
        super().listar_atracoes()

    @task(3)
    def gerar_roteiro(self):
        if self.garantir_autenticacao():
            super().gerar_roteiro()

    @task(2)
    def listar_roteiros(self):
        if self.garantir_autenticacao():
            super().listar_roteiros()


# Impede a execução independente da classe original.
UsuarioBase.abstract = True


class EstresseProgressivo(LoadTestShape):
    """
    PERF-STRESS-01:
    aumenta progressivamente a carga de usuários.
    """

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 120, "users": 25, "spawn_rate": 5},
        {"duration": 180, "users": 50, "spawn_rate": 10},
        {"duration": 240, "users": 75, "spawn_rate": 10},
        {"duration": 300, "users": 100, "spawn_rate": 10},
    ]

    def tick(self):

        tempo_execucao = self.get_run_time()

        for etapa in self.stages:

            if tempo_execucao < etapa["duration"]:

                return (
                    etapa["users"],
                    etapa["spawn_rate"],
                )

        return None
