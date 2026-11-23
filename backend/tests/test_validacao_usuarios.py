import pytest
from pydantic import ValidationError

from app.schemas.usuario import UsuarioCreate
from app.schemas.auth import LoginRequest
from app.schemas.preferencias import PreferenciasCreate


@pytest.mark.parametrize(
    "nome, email, senha",
    [
        ("Bruna", "bruna@example.com", "senha123"),
        ("Ana", "ana@example.com", "12345678"),
        ("Joao Silva", "joao@example.com", "senhaSegura123"),
    ],
)
def test_cadastro_usuario_valido(nome, email, senha):
    usuario = UsuarioCreate(
        nome=nome,
        email=email,
        senha=senha,
        aceita_termos=True,
        aceita_privacidade=True,
    )

    assert usuario.nome == nome
    assert str(usuario.email) == email
    assert usuario.senha == senha


@pytest.mark.parametrize(
    "nome, email, senha",
    [
        ("A", "ana@example.com", "senha123"),
        ("", "ana@example.com", "senha123"),
        ("Ana", "email-invalido", "senha123"),
        ("Ana", "ana@example.com", "1234567"),
        ("Ana", "ana@example.com", ""),
    ],
)
def test_cadastro_usuario_invalido(nome, email, senha):
    with pytest.raises(ValidationError):
        UsuarioCreate(
            nome=nome,
            email=email,
            senha=senha,
            aceita_termos=True,
            aceita_privacidade=True,
        )


def test_cadastro_exige_aceites_explicitos():
    with pytest.raises(ValidationError):
        UsuarioCreate(
            nome="Ana",
            email="ana@example.com",
            senha="senha123",
            aceita_termos=False,
            aceita_privacidade=False,
        )


@pytest.mark.parametrize(
    "email, senha",
    [
        ("bruna@example.com", "senha123"),
        ("ana@example.com", "12345678"),
    ],
)
def test_dados_login_validos(email, senha):
    login = LoginRequest(email=email, senha=senha)

    assert str(login.email) == email
    assert login.senha == senha


@pytest.mark.parametrize(
    "email, senha",
    [
        ("email-invalido", "senha123"),
        ("", "senha123"),
    ],
)
def test_dados_login_invalidos(email, senha):
    with pytest.raises(ValidationError):
        LoginRequest(email=email, senha=senha)


@pytest.mark.parametrize(
    "orcamento, interesses",
    [
        (0, []),
        (50, ["Museu"]),
        (150.50, ["Museu", "Parque"]),
    ],
)
def test_preferencias_validas(orcamento, interesses):
    preferencias = PreferenciasCreate(
        orcamento_maximo=orcamento,
        interesses=interesses,
    )

    assert preferencias.orcamento_maximo == orcamento
    assert preferencias.interesses == interesses


@pytest.mark.parametrize(
    "orcamento",
    [
        -1,
        -0.01,
        -100,
    ],
)
def test_preferencias_orcamento_invalido(orcamento):
    with pytest.raises(ValidationError):
        PreferenciasCreate(
            orcamento_maximo=orcamento,
            interesses=["Museu"],
        )
