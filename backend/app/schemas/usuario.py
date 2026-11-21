from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    email: EmailStr
    senha: str = Field(min_length=8)


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class AlterarSenhaRequest(BaseModel):
    senha_atual: str = Field(min_length=1)
    nova_senha: str = Field(min_length=8)
