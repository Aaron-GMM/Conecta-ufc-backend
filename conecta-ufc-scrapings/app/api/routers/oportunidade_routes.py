# app/api/routers/oportunidade_routes.py
import math
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from app.db.database import get_db
from app.models.oportunidade import OportunidadeDB
from app.schemas.oportunidade import PaginatedOportunidadeResponse

router = APIRouter(prefix="/api/oportunidades", tags=["Oportunidades"])


@router.get("/", response_model=PaginatedOportunidadeResponse)
def listar_oportunidades(
        page: int = Query(1, ge=1, description="Número da página atual"),
        size: int = Query(20, ge=1, le=100, description="Quantidade de itens por página"),
        db: Session = Depends(get_db)
):
    """
    Retorna as vagas de forma paginada, incluindo metadados e os resultados aninhados.
    """
    total_elements = db.query(OportunidadeDB).count()
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 0
    offset = (page - 1) * size

    # Usamos joinedload para buscar as oportunidades e os seus resultados de uma vez só!
    vagas = (
        db.query(OportunidadeDB)
        .options(joinedload(OportunidadeDB.resultados))
        .offset(offset)
        .limit(size)
        .all()
    )

    return {
        "data": vagas,
        "meta": {
            "total_elements": total_elements,
            "total_pages": total_pages,
            "current_page": page,
            "size": size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    }