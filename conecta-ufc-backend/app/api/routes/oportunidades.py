import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.oportunidade import OportunidadeResponse
from app.services.oportunidade_service import listar_oportunidades_ordenadas

router = APIRouter(prefix="/oportunidades", tags=["oportunidades"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[OportunidadeResponse])
def listar_oportunidades(db: Session = Depends(get_db)):
    """
    Retorna as oportunidades já coletadas e cadastradas no banco central,
    ordenadas pela data de encerramento.
    """
    try:
        return listar_oportunidades_ordenadas(db)
    except SQLAlchemyError as exc:
        logger.exception("Erro ao listar oportunidades")
        raise HTTPException(
            status_code=500,
            detail="Erro ao listar oportunidades. Tente novamente em alguns instantes.",
        ) from exc
