from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.oportunidade import OportunidadeDB
from app.schemas.oportunidade import OportunidadeResponse

router = APIRouter(prefix="/oportunidades", tags=["oportunidades"])

@router.get("", response_model=List[OportunidadeResponse])
def listar_oportunidades(db: Session = Depends(get_db)):
    """
    Retorna a lista de oportunidades cadastradas no banco central.
    """
    return db.query(OportunidadeDB).all()
