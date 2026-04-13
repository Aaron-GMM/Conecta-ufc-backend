from pydantic import BaseModel
from typing import Optional

class OportunidadeBase(BaseModel):
    titulo: str
    origem: str
    tipo: str
    link: str
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None

class ResultadoBase(BaseModel):
    titulo: str
    origem: str
    tipo: str
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    resultado: str