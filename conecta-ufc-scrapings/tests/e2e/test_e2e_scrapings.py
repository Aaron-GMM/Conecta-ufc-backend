import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine, get_db

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_e2e = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocalE2E = sessionmaker(autocommit=False, autoflush=False, bind=engine_e2e)

@pytest.fixture(scope="module")
def e2e_db_session():
    from app.models.oportunidade import OportunidadeDB, ResultadoDB
    Base.metadata.create_all(bind=engine_e2e)
    session = TestingSessionLocalE2E()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_e2e)

@pytest.fixture(scope="module")
def e2e_client(e2e_db_session):
    def override_get_db():
        try:
            yield e2e_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_e2e_scraper_sync(e2e_client):
    """
    Testa a chamada de sincronização sem mocks.
    Atenção: Esse teste de fato pode engatilhar requisições na rede.
    """
    response = e2e_client.post("/api/scrapers/sync")
    assert response.status_code == 200
    assert response.json() == {"status": "Sincronização iniciada manualmente"}

def test_e2e_listar_oportunidades_e2e(e2e_client):
    response = e2e_client.get("/api/oportunidades/")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)

def test_e2e_listar_resultados_e2e(e2e_client):
    response = e2e_client.get("/api/resultados/")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)

# We avoid running full UFC and FASTEF scrapers here to not spam the servers in E2E 
# unless explicitly needed, since /sync already tests the flow internally.
