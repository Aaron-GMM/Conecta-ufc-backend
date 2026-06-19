from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Union
from datetime import datetime


class ResultadoResponse(BaseModel):
    id: int
    titulo: str
    link: str
    data_publicacao: Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)


class OportunidadeResponse(BaseModel):
    id: int
    titulo: str
    origem: str
    tipo: str
    link: str
    data_inicio: Optional[Union[datetime, str]] = None
    data_fim: Optional[Union[datetime, str]] = None
    remuneracao: Optional[Union[float, str]] = None
    vagas: Optional[Union[int, str]] = None
    coordenador: Optional[str] = None
    descricao: Optional[str] = None
    data_criacao: Optional[Union[datetime, str]] = None

    resultados: List[ResultadoResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaginatedMeta(BaseModel):
    total_elements: int
    total_pages: int
    current_page: int
    size: int
    has_next: bool
    has_previous: bool

class PaginatedOportunidadeResponse(BaseModel):
    data: List[OportunidadeResponse]
    meta: PaginatedMeta

class FavoritoResponse(BaseModel):
    id: int
    usuario_id: str
    oportunidade_id: int
    data_favoritado: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas para Sincronização (Ingestão)
class ResultadoSync(BaseModel):
    titulo: str
    link: str

class OportunidadeSync(BaseModel):
    titulo: str
    origem: str
    tipo: str
    link: str
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    remuneracao: Optional[float] = None
    vagas: Optional[int] = None
    coordenador: Optional[str] = None
    descricao: Optional[str] = None
    resultados: List[ResultadoSync] = Field(default_factory=list)
