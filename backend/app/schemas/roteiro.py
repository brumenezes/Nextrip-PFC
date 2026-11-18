
from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Dados recebidos para gerar um roteiro de um dia
class GerarRoteiroRequest(BaseModel):
    data_visita: date

    tempo_disponivel_minutos: int = Field(
        gt=0,
        description="Tempo disponível para visitar atrações"
    )

    orcamento_maximo: float = Field(
        ge=0,
        description="Orçamento máximo para as atrações"
    )


# Informações de cada atração selecionada
class AtividadeRoteiroResponse(BaseModel):
    poi_id: UUID
    nome: str
    categoria: str | None = None
    ordem_sequencia: int
    preco_estimado: float
    duracao_minutos: int


# Resposta da geração do roteiro
class GerarRoteiroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roteiro_id: UUID
    data_visita: date

    tempo_disponivel_minutos: int
    tempo_total_visitas: int

    orcamento_maximo: float
    custo_total_estimado: float

    atividades: list[AtividadeRoteiroResponse]
