from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


def test_home_retorna_mensagem_de_boas_vindas():
    with TestClient(app) as cliente:
        resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert resposta.json() == {"mensagem": "Bem-vindo à API do NexTrip!"}


def test_health_retorna_status_ok():
    with TestClient(app) as cliente:
        resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "servico": "NexTrip Backend"}


def test_health_db_confirma_conexao():
    banco = MagicMock()
    app.dependency_overrides[get_db] = lambda: banco

    try:
        with TestClient(app) as cliente:
            resposta = cliente.get("/health/db")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
        "banco": "PostgreSQL",
        "conexao": "ativa",
    }
    banco.execute.assert_called_once()


def test_health_db_retorna_503_quando_banco_falha():
    banco = MagicMock()
    banco.execute.side_effect = RuntimeError("falha simulada")
    app.dependency_overrides[get_db] = lambda: banco

    try:
        with TestClient(app) as cliente:
            resposta = cliente.get("/health/db")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resposta.status_code == 503
    assert resposta.json() == {"detail": "Banco de dados indisponível"}
