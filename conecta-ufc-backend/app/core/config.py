from os import getenv
from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env da raiz do backend
load_dotenv()

class Settings:
    keycloak_server_url: str = getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080/")
    keycloak_realm: str = getenv("KEYCLOAK_REALM", "conecta-ufc")
    keycloak_client_id: str = getenv("KEYCLOAK_CLIENT_ID", "conecta-ufc-backend")
    keycloak_client_secret: str | None = getenv("KEYCLOAK_CLIENT_SECRET")
    frontend_origin: str = getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    database_url: str | None = getenv("DATABASE_URL")
    sync_api_key: str = getenv("SYNC_API_KEY", "conecta-ufc-dev-key")

settings = Settings()
