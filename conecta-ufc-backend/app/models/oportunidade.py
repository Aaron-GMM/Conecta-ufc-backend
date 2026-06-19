from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
from sqlalchemy import UniqueConstraint


class OportunidadeDB(Base):
    __tablename__ = "oportunidades"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, index=True)
    origem = Column(String)
    tipo = Column(String)
    link = Column(String, unique=True, index=True)
    
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    
    remuneracao = Column(Float, nullable=True)
    vagas = Column(Integer, nullable=True)
    coordenador = Column(String, nullable=True)
    descricao = Column(String, nullable=True)

    data_criacao = Column(DateTime, default=datetime.utcnow)

    resultados = relationship("ResultadoDB", back_populates="oportunidade", cascade="all, delete-orphan")
    favoritos = relationship("FavoritoDB", back_populates="oportunidade", cascade="all, delete-orphan")


class ResultadoDB(Base):
    __tablename__ = "resultados"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    link = Column(String, unique=True)
    data_publicacao = Column(DateTime, default=datetime.utcnow)

    oportunidade_id = Column(Integer, ForeignKey("oportunidades.id"))
    oportunidade = relationship("OportunidadeDB", back_populates="resultados")


class FavoritoDB(Base):
    __tablename__ = "favoritos"
    __table_args__ = (
          UniqueConstraint("usuario_id", "oportunidade_id", name="uq_favorito_usuario_oportunidade"),
    )

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(String, nullable=False)
    oportunidade_id = Column(Integer, ForeignKey("oportunidades.id"), nullable=False)
    data_favoritado = Column(DateTime, default=datetime.utcnow)
    oportunidade = relationship("OportunidadeDB")
