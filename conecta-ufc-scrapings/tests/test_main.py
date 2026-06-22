import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app, job_automacao

client = TestClient(app)

def test_read_root_retorna_mensagem():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API Conecta UFC está rodando!"}

@patch("app.main.SessionLocal")
@patch("app.main.rodar_scraper_ufc")
@patch("app.main.rodar_scraper_fastef")
@patch("app.main.SyncService")
def test_job_automacao_roda_scrapers_e_sync(mock_sync, mock_fastef, mock_ufc, mock_db):
    mock_session = MagicMock()
    mock_db.return_value = mock_session
    mock_sync_instance = MagicMock()
    mock_sync.return_value = mock_sync_instance
    
    job_automacao()
    
    mock_ufc.assert_called_once_with(mock_session)
    mock_fastef.assert_called_once_with(mock_session)
    mock_sync_instance.sync.assert_called_once()
    mock_session.close.assert_called_once()

@patch("app.main.SessionLocal")
@patch("app.main.rodar_scraper_ufc")
def test_job_automacao_com_erro_fecha_banco(mock_ufc, mock_db):
    mock_session = MagicMock()
    mock_db.return_value = mock_session
    mock_ufc.side_effect = Exception("Erro forçado")
    
    job_automacao()
    
    mock_session.close.assert_called_once()

@patch("app.main.BackgroundScheduler")
def test_lifespan_inicializa_e_desliga_scheduler(mock_scheduler):
    mock_instance = MagicMock()
    mock_scheduler.return_value = mock_instance
    
    with TestClient(app):
        pass
    
    mock_instance.start.assert_called_once()
    mock_instance.shutdown.assert_called_once()
