from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


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


class UsuarioUpdate(BaseModel):
    email: EmailStr | None = None
    nome: str | None = Field(default=None, min_length=1)
    preferencias: list[str] | None = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, nome: str | None):
        if nome is not None and not nome.strip():
            raise ValueError("O nome nao pode ser vazio")
        return nome.strip() if nome is not None else None

    @model_validator(mode="after")
    def validar_campo_informado(self):
        if self.email is None and self.nome is None and self.preferencias is None:
            raise ValueError("Informe ao menos um campo para atualizar")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str
