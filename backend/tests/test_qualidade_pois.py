import pytest

from app.services.qualidade_pois import nome_poi_e_util


@pytest.mark.parametrize("nome", ["Abertura", "Entrada", "Saída", "Sem nome", "yes"])
def test_rejeita_nomes_genericos(nome):
    assert nome_poi_e_util(nome) is False


@pytest.mark.parametrize("nome", ["Arena B3", "Casa da Imagem", "Galeria Florêncio"])
def test_mantem_nomes_descritivos(nome):
    assert nome_poi_e_util(nome) is True
