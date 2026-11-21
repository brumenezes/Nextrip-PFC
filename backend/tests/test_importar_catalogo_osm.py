import json

import pytest

from scripts.importar_catalogo_osm import carregar_catalogo, transformar_atracao


def atracao_valida():
    return {
        "id": "osm:node:123",
        "nome": "Museu Teste",
        "categoria": "Museu",
        "lat": -23.55,
        "lon": -46.63,
        "duracao_min": 70,
        "origem_dado": "OpenStreetMap",
    }


def test_transformar_atracao_preserva_identificador_completo():
    atracao = transformar_atracao(atracao_valida(), preco_padrao=12.5)

    assert atracao.osm_id == 123
    assert atracao.identificador == "osm:node:123"
    assert atracao.categoria == "museu"
    assert atracao.preco_estimado == 12.5
    assert atracao.dados_brutos["identificador"] == "osm:node:123"


def test_carregar_catalogo_exige_atribuicao_osm(tmp_path):
    caminho = tmp_path / "catalogo.json"
    caminho.write_text(
        json.dumps({
            "metadados": {"fonte": "OpenStreetMap", "atribuicao": "sem crédito"},
            "atracoes": [atracao_valida()],
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="atribuição"):
        carregar_catalogo(caminho)


def test_carregar_catalogo_valido(tmp_path):
    caminho = tmp_path / "catalogo.json"
    caminho.write_text(
        json.dumps({
            "metadados": {
                "fonte": "OpenStreetMap",
                "atribuicao": "© OpenStreetMap contributors",
            },
            "atracoes": [atracao_valida()],
        }),
        encoding="utf-8",
    )

    assert len(carregar_catalogo(caminho)) == 1
