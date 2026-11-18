
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PreferenciasCreate(BaseModel):
    orcamento_maximo: float = Field(ge=0)


class PreferenciasResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    orcamento_maximo: float | None

    model_config = ConfigDict(from_attributes=True)
