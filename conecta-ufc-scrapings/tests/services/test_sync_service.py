import pytest
from unittest.mock import patch, MagicMock
from app.services.sync_service import SyncService
import requests

@pytest.fixture
def sync_service():
    with patch("app.services.sync_service.os.getenv") as mock_getenv:
        mock_getenv.side_effect = lambda k: "http://core.api" if k == "CORE_API_URL" else "API_KEY_TEST"
        yield SyncService()

class MockOportunidade:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.sincronizado = 0

class MockResultado:
    def __init__(self, titulo, link):
        self.titulo = titulo
        self.link = link

# --- Testes para sync ---

@patch("app.services.sync_service.SessionLocal")
def test_sync_sem_vagas_retorna_antecipado(mock_session_local, sync_service):
    # Arrange
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.all.return_value = []
    
    # Act
    sync_service.sync()
    
    # Assert
    mock_db.query.assert_called_once()
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()

@patch("app.services.sync_service.requests.post")
@patch("app.services.sync_service.SessionLocal")
def test_sync_com_vagas_e_sucesso_na_api_atualiza_banco(mock_session_local, mock_post, sync_service):
    # Arrange
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    # Criando vaga mockada
    res1 = MockResultado("Res 1", "http://res1.com")
    vaga = MockOportunidade(
        titulo="Vaga Teste",
        origem="UFC",
        tipo="Bolsa",
        link="http://link.com",
        data_inicio=None,
        data_fim=None,
        remuneracao=100.0,
        vagas=1,
        resultados=[res1]
    )
    mock_filter.all.return_value = [vaga]
    
    # Mock da resposta da API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    # Act
    sync_service.sync()
    
    # Assert
    mock_post.assert_called_once()
    assert vaga.sincronizado == 1
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()

@patch("app.services.sync_service.requests.post")
@patch("app.services.sync_service.SessionLocal")
def test_sync_com_vagas_mas_erro_na_api_nao_atualiza_banco(mock_session_local, mock_post, sync_service):
    # Arrange
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    vaga = MockOportunidade(
        titulo="Vaga Falha", origem="UFC", tipo="Bolsa", link="url",
        data_inicio=None, data_fim=None, remuneracao=None, vagas=None, resultados=[]
    )
    mock_filter.all.return_value = [vaga]
    
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response
    
    # Act
    sync_service.sync()
    
    # Assert
    mock_post.assert_called_once()
    assert vaga.sincronizado == 0  # Não alterou
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()

@patch("app.services.sync_service.requests.post")
@patch("app.services.sync_service.SessionLocal")
def test_sync_excecao_inesperada_garante_fechamento_do_banco(mock_session_local, mock_post, sync_service):
    # Arrange
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    vaga = MockOportunidade(
        titulo="Vaga Exception", origem="UFC", tipo="Bolsa", link="url",
        data_inicio=None, data_fim=None, remuneracao=None, vagas=None, resultados=[]
    )
    mock_filter.all.return_value = [vaga]
    
    # Força exceção
    mock_post.side_effect = requests.exceptions.ConnectionError("Sem rede")
    
    # Act
    sync_service.sync()
    
    # Assert
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()
