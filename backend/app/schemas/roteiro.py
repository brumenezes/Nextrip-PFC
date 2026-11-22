
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Dados recebidos para gerar um roteiro de um dia
class GerarRoteiroRequest(BaseModel):
    data_visita: date

    tempo_disponivel_minutos: int = Field(
        gt=0,
        le=2_147_483_647,
        description="Tempo disponível para visitar atrações"
    )

    orcamento_maximo: float = Field(
        ge=0,
        allow_inf_nan=False,
        description="Orçamento máximo para as atrações"
    )

    quantidade_paradas: int | None = Field(
        default=None,
        ge=1,
        le=19,
        description="Quantidade exata de atrações para a rota otimizada",
    )
    latitude_origem: float | None = Field(default=None, ge=-90, le=90)
    longitude_origem: float | None = Field(default=None, ge=-180, le=180)
    peso_preferencias: float = Field(default=0.8, ge=0, le=1)
    usar_matriz_viaria: bool = False
    metrica_recomendacao: Literal["cosseno", "hibrido"] = "cosseno"
    peso_cosseno: float = Field(default=0.7, ge=0, le=1)
    retornar_origem: bool = False

    @model_validator(mode="after")
    def validar_origem_completa(self):
        if (self.latitude_origem is None) != (self.longitude_origem is None):
            raise ValueError("Latitude e longitude de origem devem ser informadas juntas")
        if self.retornar_origem and self.latitude_origem is None:
            raise ValueError("Informe a origem para incluir o retorno")
        return self


# Informações de cada atração selecionada
class AtividadeRoteiroResponse(BaseModel):
    poi_id: UUID
    nome: str
    categoria: str | None = None
    ordem_sequencia: int
    preco_estimado: float
    duracao_minutos: int
    tempo_deslocamento_previsto: int = 0
    distancia_deslocamento_metros: float = 0.0


# Resposta da geração do roteiro
class GerarRoteiroResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roteiro_id: UUID
    data_visita: date
    tempo_disponivel_minutos: int
    tempo_total_visitas: int
    orcamento_maximo: float
    custo_total_estimado: float
    tempo_total_deslocamentos: int = 0
    tempo_total_roteiro: int = 0
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

