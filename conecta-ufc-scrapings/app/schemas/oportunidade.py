# app/schemas/oportunidade.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class ResultadoResponse(BaseModel):
    id: int
    titulo: str
    link: str
    data_publicacao: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OportunidadeResponse(BaseModel):
    id: int
    titulo: str
    origem: str
    tipo: str
    link: str
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None

    # NOVOS CAMPOS NA RESPOSTA
    remuneracao: Optional[float] = None
    vagas: Optional[int] = None
    coordenador: Optional[str] = None
    descricao: Optional[str] = None

    data_criacao: Optional[datetime] = None

    resultados: List[ResultadoResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedOportunidadeResponse(BaseModel):
    data: List[OportunidadeResponse]
    meta: dict


class PaginatedResultadoResponse(BaseModel):
    data: List[ResultadoResponse]
    meta: dict