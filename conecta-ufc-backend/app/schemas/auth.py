from pydantic import BaseModel, EmailStr


class UsuarioAutenticado(BaseModel):
    sub: str
    email: EmailStr | None = None
    preferred_username: str | None = None
