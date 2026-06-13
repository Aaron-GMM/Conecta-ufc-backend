from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1)
    email: EmailStr
    senha: str = Field(min_length=6)
    curso: str = Field(min_length=1)
    oportunidades: list[str]


class UsuarioResponse(BaseModel):
    id: str
    email: EmailStr
    nome: str
    curso: str
    oportunidades: list[str]


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str
