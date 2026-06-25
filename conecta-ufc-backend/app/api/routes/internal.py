from fastapi import APIRouter, Depends, HTTPException, Security, status, BackgroundTasks
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.config import settings
from app.models.oportunidade import OportunidadeDB, ResultadoDB
from app.schemas.oportunidade import OportunidadeSync
from app.services.data_quality import filtrar_oportunidades_qualificadas
from app.services.alerta_service import disparar_alerta_nova_oportunidade, alertar_oportunidades_proximas_do_fim

router = APIRouter(prefix="/internal", tags=["internal"])

API_KEY_NAME = "X-Sync-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == settings.sync_api_key:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Chave de sincronização inválida."
    )

@router.post("/sync", status_code=status.HTTP_200_OK)
def sync_data(
    data: List[OportunidadeSync],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Rota de ingestão de dados para sincronização entre Worker e Backend Core.
    """
    oportunidades_novas = 0
    resultados_novos = 0
    
    # 1. Filtro de Qualidade de Dados
    # Remove oportunidades muito defasadas (vazias) ou com links inacessíveis/bloqueados
    data_qualificada = filtrar_oportunidades_qualificadas(data)
    
    # Registra quantas foram descartadas
    oportunidades_descartadas = len(data) - len(data_qualificada)

    for item in data_qualificada:
        # Busca oportunidade pelo link (único)
        vaga_db = db.query(OportunidadeDB).filter(OportunidadeDB.link == item.link).first()

        if not vaga_db:
            vaga_db = OportunidadeDB(
                titulo=item.titulo,
                origem=item.origem,
                tipo=item.tipo,
                link=item.link,
                data_inicio=item.data_inicio,
                data_fim=item.data_fim,
                remuneracao=item.remuneracao,
                vagas=item.vagas,
                coordenador=item.coordenador,
                descricao=item.descricao
            )
            db.add(vaga_db)
            db.flush()  # Para obter o ID
            oportunidades_novas += 1
            
            # Dispara alerta de nova oportunidade em background
            if vaga_db.tipo:
                background_tasks.add_task(disparar_alerta_nova_oportunidade, vaga_db.tipo, vaga_db.titulo, vaga_db.link)
        else:
            # Atualiza dados caso já exista, para não perder coordenador e descricao
            vaga_db.titulo = item.titulo
            vaga_db.origem = item.origem
            vaga_db.tipo = item.tipo
            vaga_db.data_inicio = item.data_inicio
            vaga_db.data_fim = item.data_fim
            vaga_db.remuneracao = item.remuneracao
            vaga_db.vagas = item.vagas
            vaga_db.coordenador = item.coordenador
            vaga_db.descricao = item.descricao
        
        # Sincroniza resultados
        for res in item.resultados:
            existe_res = db.query(ResultadoDB).filter(ResultadoDB.link == res.link).first()
            if not existe_res:
                novo_res = ResultadoDB(
                    titulo=res.titulo,
                    link=res.link,
                    oportunidade_id=vaga_db.id
                )
                db.add(novo_res)
                resultados_novos += 1

    db.commit()
    return {
        "status": "sucesso",
        "oportunidades_recebidas": len(data),
        "oportunidades_descartadas": oportunidades_descartadas,
        "oportunidades_novas": oportunidades_novas,
        "resultados_novos": resultados_novos
    }

@router.post("/cron/alertas-vencimento", status_code=status.HTTP_200_OK)
def trigger_alertas_vencimento(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Rota para ser chamada via Cron para verificar e alertar sobre oportunidades vencendo.
    """
    background_tasks.add_task(alertar_oportunidades_proximas_do_fim, db)
    return {"status": "sucesso", "mensagem": "Verificação de alertas iniciada em background"}
