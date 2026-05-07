import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.oportunidade import ResultadoDB
from app.schemas.oportunidade import ResultadoResponse, PaginatedResultadoResponse

router = APIRouter(prefix="/api/resultados", tags=["Resultados"])


@router.get("/", response_model=PaginatedResultadoResponse)
def listar_resultados(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        busca: str = Query(None, description="Busca por título do resultado"),
        db: Session = Depends(get_db)
):
    query = db.query(ResultadoDB)

    if busca:
        query = query.filter(ResultadoDB.titulo.ilike(f"%{busca}%"))

    total_elements = query.count()
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 0
    offset = (page - 1) * size

    resultados = query.offset(offset).limit(size).all()

    return {
        "data": resultados,
        "meta": {
            "total_elements": total_elements,
            "total_pages": total_pages,
            "current_page": page,
            "size": size
        }
    }


@router.get("/{resultado_id}", response_model=ResultadoResponse)
def obter_resultado(resultado_id: int, db: Session = Depends(get_db)):
    """
    Retorna os detalhes de um resultado específico.
    """
    resultado = db.query(ResultadoDB).filter(ResultadoDB.id == resultado_id).first()
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado não encontrado")
    return resultado