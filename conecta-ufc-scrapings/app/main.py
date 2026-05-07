from fastapi import FastAPI
from app.api.routers import oportunidade_routes, scraper_routes, resultado_routes # Importe aqui
from app.db.database import engine, Base

# Cria as tabelas se não existirem (embora estejamos usando Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Conecta UFC API")

# Registro dos roteadores
app.include_router(oportunidade_routes.router)
app.include_router(scraper_routes.router)
app.include_router(resultado_routes.router) # Adicione esta linha

@app.get("/")
def read_root():
    return {"message": "API Conecta UFC está rodando!"}