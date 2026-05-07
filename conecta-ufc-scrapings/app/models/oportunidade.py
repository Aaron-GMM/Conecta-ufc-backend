from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relação 1:N com resultados
    resultados = relationship("ResultadoDB", back_populates="oportunidade", cascade="all, delete-orphan")


class ResultadoDB(Base):
    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)  # Ex: "Resultado Final", "Aditivo 01"
    link = Column(String, unique=True)
    data_publicacao = Column(DateTime, default=datetime.utcnow)

    # Chave estrangeira para a oportunidade pai
    oportunidade_id = Column(Integer, ForeignKey("oportunidades.id"))

    oportunidade = relationship("OportunidadeDB", back_populates="resultados")