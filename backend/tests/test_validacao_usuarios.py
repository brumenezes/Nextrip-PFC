import pytest
from pydantic import ValidationError

from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
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

@pytest.mark.parametrize(
    "tamanho, valido",
    [
        pytest.param(1, False, id="AVL-01"),
        pytest.param(2, True, id="AVL-02"),
        pytest.param(3, True, id="AVL-03"),
        pytest.param(149, True, id="AVL-04"),
        pytest.param(150, True, id="AVL-05"),
        pytest.param(151, False, id="AVL-06"),
    ],
)
def test_valor_limite_nome(tamanho, valido):
    dados = {
        "nome": "A" * tamanho,
        "email": "ana@example.com",
        "senha": "senha123",
        "aceita_termos": True,
        "aceita_privacidade": True,
    }

    if valido:
        usuario = UsuarioCreate(**dados)
        assert len(usuario.nome) == tamanho
    else:
        with pytest.raises(ValidationError) as erro:
            UsuarioCreate(**dados)

        assert {e["loc"] for e in erro.value.errors()} == {
            ("nome",)
        }

@pytest.mark.parametrize(
    "tamanho, valido",
    [
        pytest.param(7, False, id="AVL-07"),
        pytest.param(8, True, id="AVL-08"),
        pytest.param(9, True, id="AVL-09"),
    ],
)
def test_valor_limite_senha(tamanho, valido):
    dados = {
        "nome": "Ana",
        "email": "ana@example.com",
        "senha": "a" * tamanho,
        "aceita_termos": True,
        "aceita_privacidade": True,
    }

    if valido:
        usuario = UsuarioCreate(**dados)
        assert len(usuario.senha) == tamanho
    else:
        with pytest.raises(ValidationError) as erro:
            UsuarioCreate(**dados)

        assert {e["loc"] for e in erro.value.errors()} == {
            ("senha",)
        }

@pytest.mark.parametrize(
    "campo, valor, remover",
    [
        pytest.param(
            "email", "", False, id="CE-02-email-vazio"
        ),
        pytest.param(
            "aceita_termos", False, False, id="CE-04-termos-falso"
        ),
        pytest.param(
            "aceita_termos", None, True, id="CE-04-termos-ausente"
        ),
        pytest.param(
            "aceita_privacidade", False, False,
            id="CE-05-privacidade-falso"
        ),
        pytest.param(
            "aceita_privacidade", None, True,
            id="CE-05-privacidade-ausente"
        ),
    ],
)
def test_classes_equivalencia_cadastro(campo, valor, remover):
    dados = {
        "nome": "Ana",
        "email": "ana@example.com",
        "senha": "senha123",
        "aceita_termos": True,
        "aceita_privacidade": True,
    }

    if remover:
        dados.pop(campo)
    else:
        dados[campo] = valor

    with pytest.raises(ValidationError) as erro:
        UsuarioCreate(**dados)

    assert {e["loc"] for e in erro.value.errors()} == {
        (campo,)
    }

@pytest.mark.parametrize(
    "nome",
    [
        pytest.param("   ", id="nome-apenas-espacos"),
        pytest.param(" A ", id="nome-curto-apos-normalizacao"),
    ],
)
def test_cadastro_nome_invalido_apos_normalizacao(nome):
    with pytest.raises(ValidationError) as erro:
        UsuarioCreate(
            nome=nome,
            email="ana@example.com",
            senha="senha123",
            aceita_termos=True,
            aceita_privacidade=True,
        )

    assert {e["loc"] for e in erro.value.errors()} == {
        ("nome",)
    }

@pytest.mark.parametrize(
    "nome",
    [
        pytest.param("   ", id="nome-apenas-espacos"),
        pytest.param(" A ", id="nome-curto-apos-normalizacao"),
    ],
)
def test_atualizacao_nome_invalido_apos_normalizacao(nome):
    with pytest.raises(ValidationError) as erro:
        UsuarioUpdate(
            nome=nome,
            email="ana@example.com",
        )

    assert {e["loc"] for e in erro.value.errors()} == {
        ("nome",)
    }


@pytest.mark.parametrize(
    "nome, esperado",
    [
        ("  Ana  ", "Ana"),
        ("Ana   Silva", "Ana Silva"),
    ],
)
def test_normalizacao_nome_valido(nome, esperado):
    usuario = UsuarioCreate(
        nome=nome,
        email="ana@example.com",
        senha="senha123",
        aceita_termos=True,
        aceita_privacidade=True,
    )

    atualizacao = UsuarioUpdate(
        nome=nome,
        email="ana@example.com",
    )

    assert usuario.nome == esperado
    assert atualizacao.nome == esperado