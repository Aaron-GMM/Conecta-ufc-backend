import math
import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from app.db.database import get_db
from app.core.auth import get_current_user_id
from app.models.oportunidade import OportunidadeDB, FavoritoDB
from app.schemas.oportunidade import OportunidadeResponse, PaginatedOportunidadeResponse, FavoritoResponse

router = APIRouter(prefix="/oportunidades", tags=["oportunidades"])
logger = logging.getLogger(__name__)


def aplicar_filtros_oportunidades(
    query,
    busca: Optional[str],
    origem: Optional[str],
    tipo: Optional[str],
    data_inicio: Optional[datetime],
    data_fim: Optional[datetime],
    remuneracao_min: Optional[float],
    remuneracao_max: Optional[float]
):
    if busca:
        query = query.filter(OportunidadeDB.titulo.ilike(f"%{busca}%"))
    if origem:
        query = query.filter(OportunidadeDB.origem == origem)
    if tipo:
        query = query.filter(OportunidadeDB.tipo == tipo)
    if data_inicio:
        query = query.filter(OportunidadeDB.data_inicio >= data_inicio)
    if data_fim:
        query = query.filter(OportunidadeDB.data_fim <= data_fim)
    if remuneracao_min is not None:
        query = query.filter(OportunidadeDB.remuneracao >= remuneracao_min)
    if remuneracao_max is not None:
        query = query.filter(OportunidadeDB.remuneracao <= remuneracao_max)
    return query

def paginar_resultados(query, page: int, size: int, *criterios_ordenacao):
    total_elements = query.count()
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 0
    offset = (page - 1) * size
    if not criterios_ordenacao:
        criterios_ordenacao = (
            OportunidadeDB.data_criacao.desc().nulls_last(),
            OportunidadeDB.id.desc(),
        )
    oportunidades = query.order_by(*criterios_ordenacao).offset(offset).limit(size).all()
    
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


@router.get("", response_model=PaginatedOportunidadeResponse)
def listar_oportunidades(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    busca: Optional[str] = Query(None, description="Busca por título"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (ex: UFC, FASTEF)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ex: Estágio, Monitoria)"),
    data_inicio: Optional[datetime] = Query(None, description="Filtrar a partir desta data de início"),
    data_fim: Optional[datetime] = Query(None, description="Filtrar até esta data de fim"),
    remuneracao_min: Optional[float] = Query(None, description="Remuneração mínima"),
    remuneracao_max: Optional[float] = Query(None, description="Remuneração máxima"),
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de oportunidades com filtros e paginação.
    """
    query = db.query(OportunidadeDB).options(joinedload(OportunidadeDB.resultados))
    
    query = aplicar_filtros_oportunidades(
        query, busca, origem, tipo, data_inicio, data_fim, remuneracao_min, remuneracao_max
    )

    return paginar_resultados(
        query,
        page,
        size,
        OportunidadeDB.data_criacao.desc().nulls_last(),
        OportunidadeDB.id.desc(),
    )


@router.get("/ordenadas/a-z", response_model=PaginatedOportunidadeResponse)
def listar_oportunidades_ordenadas_a_z(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    busca: Optional[str] = Query(None, description="Busca por título"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (ex: UFC, FASTEF)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ex: Estágio, Monitoria)"),
    data_inicio: Optional[datetime] = Query(None, description="Filtrar a partir desta data de início"),
    data_fim: Optional[datetime] = Query(None, description="Filtrar até esta data de fim"),
    remuneracao_min: Optional[float] = Query(None, description="Remuneração mínima"),
    remuneracao_max: Optional[float] = Query(None, description="Remuneração máxima"),
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de oportunidades com filtros, paginação e ordenação por título de A a Z.
    """
    query = db.query(OportunidadeDB).options(joinedload(OportunidadeDB.resultados))
    query = aplicar_filtros_oportunidades(
        query, busca, origem, tipo, data_inicio, data_fim, remuneracao_min, remuneracao_max
    )

    return paginar_resultados(
        query,
        page,
        size,
        func.lower(OportunidadeDB.titulo).asc().nulls_last(),
        OportunidadeDB.id.asc(),
    )


@router.get("/ordenadas/mais-recentes", response_model=PaginatedOportunidadeResponse)
def listar_oportunidades_ordenadas_por_data_recente(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    busca: Optional[str] = Query(None, description="Busca por título"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (ex: UFC, FASTEF)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ex: Estágio, Monitoria)"),
    data_inicio: Optional[datetime] = Query(None, description="Filtrar a partir desta data de início"),
    data_fim: Optional[datetime] = Query(None, description="Filtrar até esta data de fim"),
    remuneracao_min: Optional[float] = Query(None, description="Remuneração mínima"),
    remuneracao_max: Optional[float] = Query(None, description="Remuneração máxima"),
    db: Session = Depends(get_db)
):
    """
    Retorna a lista de oportunidades com filtros, paginação e ordenação da mais recente para a mais antiga.
    """
    query = db.query(OportunidadeDB).options(joinedload(OportunidadeDB.resultados))
    query = aplicar_filtros_oportunidades(
        query, busca, origem, tipo, data_inicio, data_fim, remuneracao_min, remuneracao_max
    )

    return paginar_resultados(
        query,
        page,
        size,
        OportunidadeDB.data_inicio.desc().nulls_last(),
        OportunidadeDB.data_criacao.desc().nulls_last(),
        OportunidadeDB.id.desc(),
    )

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

@router.get("/favoritos", response_model=PaginatedOportunidadeResponse)
def listar_favoritos(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    busca: Optional[str] = Query(None, description="Busca por título"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (ex: UFC, FASTEF)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ex: Estágio, Monitoria)"),
    data_inicio: Optional[datetime] = Query(None, description="Filtrar a partir desta data de início"),
    data_fim: Optional[datetime] = Query(None, description="Filtrar até esta data de fim"),
    remuneracao_min: Optional[float] = Query(None, description="Remuneração mínima"),
    remuneracao_max: Optional[float] = Query(None, description="Remuneração máxima"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todas as oportunidades favoritadas pelo usuário logado com filtros e paginação.
    """
    query = (
        db.query(OportunidadeDB)
        .join(FavoritoDB, OportunidadeDB.id == FavoritoDB.oportunidade_id)
        .filter(FavoritoDB.usuario_id == user_id)
        .options(joinedload(OportunidadeDB.resultados))
    )
    
    query = aplicar_filtros_oportunidades(
        query, busca, origem, tipo, data_inicio, data_fim, remuneracao_min, remuneracao_max
    )

    return paginar_resultados(query, page, size)


@router.get("/alertas", response_model=PaginatedOportunidadeResponse)
def listar_alertas(
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    busca: Optional[str] = Query(None, description="Busca por título"),
    origem: Optional[str] = Query(None, description="Filtrar por origem (ex: UFC, FASTEF)"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo (ex: Estágio, Monitoria)"),
    data_inicio: Optional[datetime] = Query(None, description="Filtrar a partir desta data de início"),
    data_fim: Optional[datetime] = Query(None, description="Filtrar até esta data de fim"),
    remuneracao_min: Optional[float] = Query(None, description="Remuneração mínima"),
    remuneracao_max: Optional[float] = Query(None, description="Remuneração máxima"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todas as oportunidades correspondentes aos tipos de alertas inscritos pelo usuário logado com filtros e paginação.
    """
    from app.services.keycloak_service import _criar_admin_keycloak
    
    try:
        keycloak_admin = _criar_admin_keycloak()
        user_data = keycloak_admin.get_user(user_id)
        tipos_alertas = user_data.get("attributes", {}).get("oportunidades", [])
    except Exception as e:
        logger.error(f"Erro ao buscar atributos de alerta do usuário {user_id} no Keycloak: {e}")
        tipos_alertas = []

    if not tipos_alertas:
        return {
            "data": [],
            "meta": {
                "total_elements": 0,
                "total_pages": 0,
                "current_page": page,
                "size": size,
                "has_next": False,
                "has_previous": False
            }
        }

    query = (
        db.query(OportunidadeDB)
        .filter(OportunidadeDB.tipo.in_(tipos_alertas))
        .options(joinedload(OportunidadeDB.resultados))
    )
    
    query = aplicar_filtros_oportunidades(
        query, busca, origem, tipo, data_inicio, data_fim, remuneracao_min, remuneracao_max
    )

    return paginar_resultados(query, page, size)
