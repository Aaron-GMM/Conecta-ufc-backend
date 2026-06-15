from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from app.api.routers import oportunidade_routes, scraper_routes, resultado_routes
from app.db.database import engine, Base, SessionLocal
from app.services.sync_service import SyncService
from app.api.routers.scraper_routes import rodar_scraper_ufc, rodar_scraper_fastef
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")

def job_automacao():
    """Tarefa que roda os scrapers e sincroniza os dados."""
    logger.info("Iniciando ciclo automático de raspagem e sincronização...")
    db = SessionLocal()
    try:
        # 1. Roda Scrapers
        logger.info("Executando Scraper UFC...")
        rodar_scraper_ufc(db)
        
        logger.info("Executando Scraper FASTEF...")
        rodar_scraper_fastef(db)
        
        # 2. Sincroniza
        logger.info("Iniciando Sincronização com o Core...")
        sync_service = SyncService()
        sync_service.sync()
        
    except Exception as e:
        logger.error(f"Erro no ciclo de automação: {e}")
    finally:
        db.close()
    logger.info("Ciclo de automação finalizado.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o scheduler
    scheduler = BackgroundScheduler()
    # Agenda para rodar a cada 6 horas (pode ser ajustado)
    scheduler.add_job(job_automacao, 'interval', hours=6, next_run_time=None)
    
    # Se quiser que rode uma vez logo ao iniciar, remova next_run_time=None ou use:
    # scheduler.add_job(job_automacao, 'date') # Roda agora
    
    scheduler.start()
    logger.info("Scheduler iniciado com sucesso.")
    
    yield
    
    # Desliga o scheduler ao encerrar
    scheduler.shutdown()
    logger.info("Scheduler desligado.")

app = FastAPI(title="Conecta UFC API", lifespan=lifespan)

# Registro dos roteadores
app.include_router(oportunidade_routes.router)
app.include_router(scraper_routes.router)
app.include_router(resultado_routes.router)

@app.get("/")
def read_root():
    return {"message": "API Conecta UFC está rodando!"}
