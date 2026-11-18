
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


# Resumo de um roteiro salvo
class RoteiroResumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    data_inicio: date
    data_fim: date
    custo_total_estimado: float | None = None


# Detalhes de um dia do roteiro
class RoteiroDiaResponse(BaseModel):
    data_referencia: date
    tempo_disponivel_minutos: int | None = None
    atividades: list[AtividadeRoteiroResponse]


# Resposta completa de um roteiro salvo
class RoteiroDetalhadoResponse(BaseModel):
    id: UUID
    data_inicio: date
    data_fim: date
    custo_total_estimado: float | None = None
    dias: list[RoteiroDiaResponse]

