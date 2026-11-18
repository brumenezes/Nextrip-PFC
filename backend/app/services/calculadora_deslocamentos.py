
from math import radians, sin, cos, sqrt, atan2


def calcular_distancia_metros(
    latitude_origem: float,
    longitude_origem: float,
    latitude_destino: float,
    longitude_destino: float
) -> float:
    """
    Calcula a distância geográfica aproximada
    entre duas coordenadas usando Haversine.

    Retorna a distância em metros.
    """

    raio_terra = 6371000

    lat1 = radians(latitude_origem)
    lon1 = radians(longitude_origem)
    lat2 = radians(latitude_destino)
    lon2 = radians(longitude_destino)

    diferenca_lat = lat2 - lat1
    diferenca_lon = lon2 - lon1

    a = (
        sin(diferenca_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(diferenca_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return raio_terra * c


def estimar_tempo_deslocamento(
    distancia_metros: float,
    velocidade_kmh: float = 30
) -> int:
    """
    Estima o tempo de deslocamento com base
    na distância e na velocidade média.

    Velocidade padrão: 30 km/h.

    Retorna o tempo em minutos.
    """

    if distancia_metros < 0:
        raise ValueError("A distância não pode ser negativa")

    if velocidade_kmh <= 0:
        raise ValueError("A velocidade deve ser maior que zero")

    distancia_km = distancia_metros / 1000

    tempo_horas = distancia_km / velocidade_kmh

    tempo_minutos = tempo_horas * 60

    return max(1, round(tempo_minutos)) if distancia_metros > 0 else 0
