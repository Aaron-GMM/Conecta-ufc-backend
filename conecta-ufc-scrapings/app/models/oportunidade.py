# app/models/oportunidade.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class OportunidadeDB(Base):
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    origem = Column(String)
    tipo = Column(String)
    link = Column(String, unique=True, index=True)

    # Datas (já existiam)
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)

    # NOVAS COLUNAS
    remuneracao = Column(Float, nullable=True)
    vagas = Column(Integer, nullable=True)

    data_criacao = Column(DateTime, default=datetime.utcnow)
    sincronizado = Column(Integer, default=0)  # 0 = não sincronizado, 1 = sincronizado

    resultados = relationship("ResultadoDB", back_populates="oportunidade", cascade="all, delete-orphan")


class ResultadoDB(Base):
    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    link = Column(String, unique=True)
    data_publicacao = Column(DateTime, default=datetime.utcnow)

    oportunidade_id = Column(Integer, ForeignKey("oportunidades.id"))
    oportunidade = relationship("OportunidadeDB", back_populates="resultados")