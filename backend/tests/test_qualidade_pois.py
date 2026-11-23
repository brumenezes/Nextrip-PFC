import pytest

from app.services.qualidade_pois import nome_poi_e_util


@pytest.mark.parametrize("nome", [
    "Abertura", "Acesso", "Entrada", "  PORTÃO  ", "Saída", "Sem nome",
    "Unnamed", "Yes", "No", "  A B ",
])
def test_rejeita_nomes_genericos(nome):
    assert nome_poi_e_util(nome) is False


@pytest.mark.parametrize("nome", [
    "Arena B3", "Casa da Imagem", "Galeria Florêncio",
    "Museu da Imagem e do Som", "Portão Cultural",
])
def test_mantem_nomes_descritivos(nome):
    assert nome_poi_e_util(nome) is True
