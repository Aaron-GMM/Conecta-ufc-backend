import math
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.db.database import get_db
from app.services.keycloak_service import get_current_user_id
from app.models.oportunidade import OportunidadeDB, FavoritoDB
from app.schemas.oportunidade import OportunidadeResponse, PaginatedOportunidadeResponse, FavoritoResponse

router = APIRouter(prefix="/oportunidades", tags=["oportunidades"])
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedOportunidadeResponse)
def listar_oportunidades(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    busca: Optional[str] = Query(None, description="Busca por título"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (ex: UFC, FASTEF)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ex: Estágio, Monitoria)"),
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de oportunidades com filtros e paginação.
    """
    query = db.query(OportunidadeDB).options(joinedload(OportunidadeDB.resultados))

    if busca:
        query = query.filter(OportunidadeDB.titulo.ilike(f"%{busca}%"))
    if origem:
        query = query.filter(OportunidadeDB.origem == origem)
    if tipo:
        query = query.filter(OportunidadeDB.tipo == tipo)

    total_elements = query.count()
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 0
    offset = (page - 1) * size

    oportunidades = query.order_by(OportunidadeDB.data_criacao.desc()).offset(offset).limit(size).all()

    return {
        "data": oportunidades,
        "meta": {
            "total_elements": total_elements,
            "total_pages": total_pages,
            "current_page": page,
            "size": size,
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
    }

@router.post("/{oportunidade_id}/favoritar", status_code=201)
def favoritar_oportunidade(
    oportunidade_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Marca uma oportunidade como favorita para o usuário logado.
    """
    # Verifica se a oportunidade existe
    oportunidade = db.query(OportunidadeDB).filter(OportunidadeDB.id == oportunidade_id).first()
    if not oportunidade:
        raise HTTPException(status_code=404, detail="Oportunidade não encontrada")

    # Verifica se já é favorito
    existente = db.query(FavoritoDB).filter(
        FavoritoDB.usuario_id == user_id,
        FavoritoDB.oportunidade_id == oportunidade_id
    ).first()

    if existente:
        return {"message": "Oportunidade já está nos favoritos"}

    novo_favorito = FavoritoDB(usuario_id=user_id, oportunidade_id=oportunidade_id)
    db.add(novo_favorito)
    db.commit()

    return {"message": "Oportunidade favoritada com sucesso"}

@router.delete("/{oportunidade_id}/favoritar", status_code=204)
def remover_favorito(
    oportunidade_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Remove uma oportunidade dos favoritos do usuário logado.
    """
    favorito = db.query(FavoritoDB).filter(
        FavoritoDB.usuario_id == user_id,
        FavoritoDB.oportunidade_id == oportunidade_id
    ).first()

    if not favorito:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")

    db.delete(favorito)
    db.commit()
    return None

@router.get("/favoritos", response_model=List[OportunidadeResponse])
def listar_favoritos(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todas as oportunidades favoritadas pelo usuário logado.
    """
    favoritos = db.query(FavoritoDB).filter(FavoritoDB.usuario_id == user_id).all()
    oportunidades_ids = [f.oportunidade_id for f in favoritos]
    
    return db.query(OportunidadeDB).filter(OportunidadeDB.id.in_(oportunidades_ids)).all()
