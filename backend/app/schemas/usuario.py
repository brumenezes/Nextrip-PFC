from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.privacy import PRIVACY_NOTICE_VERSION, TERMS_VERSION


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8)
    aceita_termos: Literal[True]
    aceita_privacidade: Literal[True]

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, value):
        if isinstance(value, str):
            return " ".join(value.split())

        return value

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).strip().casefold()


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    termos_versao: str = TERMS_VERSION
    termos_aceitos_em: datetime | None = None
    privacidade_versao: str = PRIVACY_NOTICE_VERSION
    privacidade_aceita_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AlterarSenhaRequest(BaseModel):
    senha_atual: str = Field(min_length=1)
    nova_senha: str = Field(min_length=8)


class UsuarioUpdate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr

    @field_validator("nome", mode="before")
    @classmethod
    def normalizar_nome(cls, value):
        if isinstance(value, str):
            return " ".join(value.split())

        return value

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).strip().casefold()
