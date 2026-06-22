import pytest
from unittest.mock import patch, MagicMock
from app.models.oportunidade import OportunidadeDB, ResultadoDB

@patch("app.api.routers.scraper_routes.UfcScraper")
def test_integration_scraper_ufc_success(mock_ufc_scraper_class, client, db_session):
    mock_instance = MagicMock()
    mock_ufc_scraper_class.return_value = mock_instance
    mock_instance.run.return_value = [
        {
            "titulo": "Bolsa Integracao UFC",
            "origem": "UFC",
            "tipo": "Bolsa",
            "link": "http://ufc.br/bolsa-int",
            "resultados": [
                {"titulo": "Resultado Integracao UFC", "link": "http://ufc.br/bolsa-int/resultado"}
            ]
        }
    ]

    response = client.post("/api/scrapers/ufc/run")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    assert data["editais_salvos"] == 1
    assert data["resultados_salvos"] == 1

    # Verifica no banco
    vaga = db_session.query(OportunidadeDB).filter_by(link="http://ufc.br/bolsa-int").first()
    assert vaga is not None
    assert vaga.titulo == "Bolsa Integracao UFC"

    resultado = db_session.query(ResultadoDB).filter_by(link="http://ufc.br/bolsa-int/resultado").first()
    assert resultado is not None
    assert resultado.oportunidade_id == vaga.id

@patch("app.api.routers.scraper_routes.FastefScraper")
def test_integration_scraper_fastef_success(mock_fastef_scraper_class, client, db_session):
    mock_instance = MagicMock()
    mock_fastef_scraper_class.return_value = mock_instance
    mock_instance.run.return_value = [
        {"titulo": "Edital 99/2026 - Teste", "origem": "FASTEF", "tipo": "Estágio", "link": "http://fastef.br/99"},
        {"titulo": "Resultado Final Edital 99/2026", "origem": "FASTEF", "tipo": "Estágio", "link": "http://fastef.br/99/res"}
    ]

    response = client.post("/api/scrapers/fastef/run")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    
    # Verifica no banco
    vaga = db_session.query(OportunidadeDB).filter_by(link="http://fastef.br/99").first()
    assert vaga is not None

    resultado = db_session.query(ResultadoDB).filter_by(link="http://fastef.br/99/res").first()
    assert resultado is not None
    assert resultado.oportunidade_id == vaga.id

@patch("app.api.routers.scraper_routes.SyncService")
def test_integration_scraper_sync(mock_sync_class, client):
    mock_instance = MagicMock()
    mock_sync_class.return_value = mock_instance
    
    response = client.post("/api/scrapers/sync")
    assert response.status_code == 200
    assert response.json() == {"status": "Sincronização iniciada manualmente"}
    mock_instance.sync.assert_called_once()
