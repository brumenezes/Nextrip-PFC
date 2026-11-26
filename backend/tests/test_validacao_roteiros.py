import pytest
from pydantic import ValidationError

from app.schemas.roteiro import GerarRoteiroRequest


def dados_roteiro_validos():
    return {
        "data_visita": "2026-12-10",
        "tempo_disponivel_minutos": 480,
        "orcamento_maximo": 200.0,
        "quantidade_paradas": 5,
        "latitude_origem": -23.5505,
        "longitude_origem": -46.6333,
        "peso_preferencias": 0.8,
        "peso_cosseno": 0.7,
        "metrica_recomendacao": "cosseno",
        "usar_matriz_viaria": False,
        "retornar_origem": False,
    }


@pytest.mark.parametrize(
    "campo, valor, valido",
    [
        # Tempo disponível
        pytest.param("tempo_disponivel_minutos", 0, False, id="AVL-10"),
        pytest.param("tempo_disponivel_minutos", 1, True, id="AVL-11"),
        pytest.param("tempo_disponivel_minutos", 2, True, id="AVL-12"),
        pytest.param("tempo_disponivel_minutos", 2147483646, True, id="AVL-13"),
        pytest.param("tempo_disponivel_minutos", 2147483647, True, id="AVL-14"),
        pytest.param("tempo_disponivel_minutos", 2147483648, False, id="AVL-15"),

        # Orçamento
        pytest.param("orcamento_maximo", -0.01, False, id="AVL-16"),
        pytest.param("orcamento_maximo", 0, True, id="AVL-17"),
        pytest.param("orcamento_maximo", 0.01, True, id="AVL-18"),

        # Quantidade de paradas
        pytest.param("quantidade_paradas", 0, False, id="AVL-19"),
        pytest.param("quantidade_paradas", 1, True, id="AVL-20"),
        pytest.param("quantidade_paradas", 2, True, id="AVL-21"),
        pytest.param("quantidade_paradas", 18, True, id="AVL-22"),
        pytest.param("quantidade_paradas", 19, True, id="AVL-23"),
        pytest.param("quantidade_paradas", 20, False, id="AVL-24"),

        # Latitude
        pytest.param("latitude_origem", -90.01, False, id="AVL-25"),
        pytest.param("latitude_origem", -90, True, id="AVL-26"),
        pytest.param("latitude_origem", -89.99, True, id="AVL-27"),
        pytest.param("latitude_origem", 89.99, True, id="AVL-28"),
        pytest.param("latitude_origem", 90, True, id="AVL-29"),
        pytest.param("latitude_origem", 90.01, False, id="AVL-30"),

        # Longitude
        pytest.param("longitude_origem", -180.01, False, id="AVL-31"),
        pytest.param("longitude_origem", -180, True, id="AVL-32"),
        pytest.param("longitude_origem", -179.99, True, id="AVL-33"),
        pytest.param("longitude_origem", 179.99, True, id="AVL-34"),
        pytest.param("longitude_origem", 180, True, id="AVL-35"),
        pytest.param("longitude_origem", 180.01, False, id="AVL-36"),

        # Peso das preferências
        pytest.param("peso_preferencias", -0.01, False, id="AVL-37"),
        pytest.param("peso_preferencias", 0, True, id="AVL-38"),
        pytest.param("peso_preferencias", 0.01, True, id="AVL-39"),
        pytest.param("peso_preferencias", 0.99, True, id="AVL-40"),
        pytest.param("peso_preferencias", 1, True, id="AVL-41"),
        pytest.param("peso_preferencias", 1.01, False, id="AVL-42"),

        # Peso do cosseno
        pytest.param("peso_cosseno", -0.01, False, id="AVL-43"),
        pytest.param("peso_cosseno", 0, True, id="AVL-44"),
        pytest.param("peso_cosseno", 0.01, True, id="AVL-45"),
        pytest.param("peso_cosseno", 0.99, True, id="AVL-46"),
        pytest.param("peso_cosseno", 1, True, id="AVL-47"),
        pytest.param("peso_cosseno", 1.01, False, id="AVL-48"),
    ],
)
def test_valores_limite_roteiro(campo, valor, valido):
    dados = dados_roteiro_validos()
    dados[campo] = valor

    if valido:
        roteiro = GerarRoteiroRequest(**dados)
        assert getattr(roteiro, campo) == valor

    else:
        with pytest.raises(ValidationError) as erro:
            GerarRoteiroRequest(**dados)

        assert {e["loc"] for e in erro.value.errors()} == {
            (campo,)
        }


@pytest.mark.parametrize(
    "campo, valor, valido, remover",
    [
        pytest.param(
            "orcamento_maximo", float("inf"), False, False,
            id="CE-09-infinito-positivo"
        ),
        pytest.param(
            "orcamento_maximo", float("-inf"), False, False,
            id="CE-09-infinito-negativo"
        ),
        pytest.param(
            "orcamento_maximo", float("nan"), False, False,
            id="CE-09-nan"
        ),
        pytest.param(
            "quantidade_paradas", None, True, True,
            id="CE-10-quantidade-ausente"
        ),
        pytest.param(
            "quantidade_paradas", None, True, False,
            id="CE-10-quantidade-nula"
        ),
        pytest.param(
            "metrica_recomendacao", "cosseno", True, False,
            id="CE-15-cosseno"
        ),
        pytest.param(
            "metrica_recomendacao", "hibrido", True, False,
            id="CE-15-hibrido"
        ),
        pytest.param(
            "metrica_recomendacao", "euclidiana", False, False,
            id="CE-15-metrica-invalida"
        ),
    ],
)
def test_classes_equivalencia_roteiro(
    campo, valor, valido, remover
):
    dados = dados_roteiro_validos()

    if remover:
        dados.pop(campo)
    else:
        dados[campo] = valor

    if valido:
        roteiro = GerarRoteiroRequest(**dados)
        assert getattr(roteiro, campo) == valor

    else:
        with pytest.raises(ValidationError) as erro:
            GerarRoteiroRequest(**dados)

        assert {e["loc"] for e in erro.value.errors()} == {
            (campo,)
        }


@pytest.mark.parametrize(
    "latitude, longitude, retorno, valido, mensagem",
    [
        pytest.param(
            None, None, False, True, None,
            id="TD-01-R1"
        ),
        pytest.param(
            None, None, True, False,
            "Informe a origem para incluir o retorno",
            id="TD-01-R2"
        ),
        pytest.param(
            None, -46.6333, False, False,
            "Latitude e longitude de origem devem ser informadas juntas",
            id="TD-01-R3"
        ),
        pytest.param(
            None, -46.6333, True, False,
            "Latitude e longitude de origem devem ser informadas juntas",
            id="TD-01-R4"
        ),
        pytest.param(
            -23.5505, None, False, False,
            "Latitude e longitude de origem devem ser informadas juntas",
            id="TD-01-R5"
        ),
        pytest.param(
            -23.5505, None, True, False,
            "Latitude e longitude de origem devem ser informadas juntas",
            id="TD-01-R6"
        ),
        pytest.param(
            -23.5505, -46.6333, False, True, None,
            id="TD-01-R7"
        ),
        pytest.param(
            -23.5505, -46.6333, True, True, None,
            id="TD-01-R8"
        ),
    ],
)
def test_tabela_decisao_origem(
    latitude, longitude, retorno, valido, mensagem
):
    dados = dados_roteiro_validos()

    dados.update(
        latitude_origem=latitude,
        longitude_origem=longitude,
        retornar_origem=retorno,
    )

    if valido:
        roteiro = GerarRoteiroRequest(**dados)

        assert roteiro.latitude_origem == latitude
        assert roteiro.longitude_origem == longitude
        assert roteiro.retornar_origem == retorno

    else:
        with pytest.raises(ValidationError) as erro:
            GerarRoteiroRequest(**dados)

        erros = erro.value.errors()

        assert len(erros) == 1
        assert erros[0]["loc"] == ()
        assert mensagem in erros[0]["msg"]


