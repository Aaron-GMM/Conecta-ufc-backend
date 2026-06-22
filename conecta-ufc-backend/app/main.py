from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import usuarios, oportunidades, internal
from app.core.config import settings
from app.core.exceptions import configure_error_handlers


app = FastAPI(title="Conecta UFC API")

configure_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router)
app.include_router(oportunidades.router)
app.include_router(internal.router)
