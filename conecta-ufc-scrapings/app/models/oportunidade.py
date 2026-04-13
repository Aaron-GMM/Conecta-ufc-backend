# app/models/oportunidade.py
from sqlalchemy import Column, Integer, String
from app.db.database import Base

class OportunidadeDB(Base):
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    origem = Column(String)
    tipo = Column(String)
    link = Column(String, unique=True, index=True) # unique para evitar duplicação
    data_inicio = Column(String, nullable=True)
    data_fim = Column(String, nullable=True)

class ResultadoDB(Base):
    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    origem = Column(String)
    tipo = Column(String)
    data_inicio = Column(String, nullable=True)
    data_fim = Column(String, nullable=True)
    resultado = Column(String)