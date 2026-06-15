import os
import requests
import logging
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.oportunidade import OportunidadeDB

logger = logging.getLogger("SyncService")

class SyncService:
    def __init__(self):
        self.api_url = os.getenv("CORE_API_URL")
        self.api_key = os.getenv("CORE_API_KEY")

    def sync(self):
        db = SessionLocal()
        try:
            # Busca oportunidades não sincronizadas
            vagas = db.query(OportunidadeDB).filter(OportunidadeDB.sincronizado == 0).all()
            
            if not vagas:
                logger.info("Nada para sincronizar.")
                return

            logger.info(f"Sincronizando {len(vagas)} oportunidades...")

            payload = []
            for vaga in vagas:
                payload.append({
                    "titulo": vaga.titulo,
                    "origem": vaga.origem,
                    "tipo": vaga.tipo,
                    "link": vaga.link,
                    "data_inicio": vaga.data_inicio.isoformat() if vaga.data_inicio else None,
                    "data_fim": vaga.data_fim.isoformat() if vaga.data_fim else None,
                    "remuneracao": vaga.remuneracao,
                    "vagas": vaga.vagas,
                    "resultados": [
                        {"titulo": r.titulo, "link": r.link} for r in vaga.resultados
                    ]
                })

            headers = {
                "X-Sync-Key": self.api_key,
                "Content-Type": "application/json"
            }

            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Marca como sincronizado
                for vaga in vagas:
                    vaga.sincronizado = 1
                db.commit()
                logger.info("Sincronização concluída com sucesso!")
            else:
                logger.error(f"Erro na sincronização: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Erro inesperado durante a sincronização: {e}")
        finally:
            db.close()
