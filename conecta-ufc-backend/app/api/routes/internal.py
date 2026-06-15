from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.config import settings
from app.models.oportunidade import OportunidadeDB, ResultadoDB
from app.schemas.oportunidade import OportunidadeSync

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
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Rota de ingestão de dados para sincronização entre Worker e Backend Core.
    """
    oportunidades_novas = 0
    resultados_novos = 0

    for item in data:
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
                vagas=item.vagas
            )
            db.add(vaga_db)
            db.flush()  # Para obter o ID
            oportunidades_novas += 1
        
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
        "oportunidades_novas": oportunidades_novas,
        "resultados_novos": resultados_novos
    }
