
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Dados necessários para cadastrar um ponto turístico
class PontoInteresseCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    categoria: str | None = None

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    preco_estimado: float | None = Field(default=None, ge=0)
    duracao_minutos: int | None = Field(default=None, gt=0)
    avaliacao_media: float | None = Field(
        default=None,
        ge=0,
        le=5
    )

    osm_id: int | None = None
    google_place_id: str | None = None


# Dados retornados pela API
class PontoInteresseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nome: str
    categoria: str | None = None

    latitude: float
    longitude: float

    preco_estimado: float | None = None
    duracao_minutos: int | None = None
    avaliacao_media: float | None = None

    osm_id: int | None = None
    google_place_id: str | None = None
