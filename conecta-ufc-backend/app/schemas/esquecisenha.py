from pydantic import BaseModel, EmailStr, Field

class EsqueciSenhaRequest(BaseModel):
    email: EmailStr
