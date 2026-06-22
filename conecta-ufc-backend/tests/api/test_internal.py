import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from app.main import app
from app.api.routes.internal import get_api_key
from app.core.config import settings

client = TestClient(app)

# --- Testes unitários para get_api_key ---

def test_get_api_key_chave_correta_retorna_chave():
    # Arrange
    chave_esperada = settings.sync_api_key
    
    # Act
    resultado = get_api_key(api_key=chave_esperada)
    
    # Assert
    assert resultado == chave_esperada

def test_get_api_key_chave_incorreta_lanca_excecao():
    # Arrange
    chave_errada = "chave_invalida_123"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_api_key(api_key=chave_errada)
        
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Chave de sincronização inválida."

def test_get_api_key_chave_vazia_lanca_excecao():
    # Arrange
    chave_vazia = ""
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_api_key(api_key=chave_vazia)
        
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Chave de sincronização inválida."

# --- Testes de Integração/Rota para /internal/sync ---

def test_sync_data_sem_api_key_retorna_403():
    # Arrange
    headers = {"Content-Type": "application/json"}
    payload = []
    
    # Act
    response = client.post("/internal/sync", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 403
    dados = response.json()
    assert dados["erro"] is True
    assert dados["mensagem"] == "Chave de sincronização inválida."

def test_sync_data_payload_invalido_retorna_422():
    # Arrange
    headers = {
        "Content-Type": "application/json",
        "X-Sync-Key": settings.sync_api_key
    }
    # Faltando os campos obrigatórios de OportunidadeSync
    payload = [{"titulo": "Vaga Incompleta"}]
    
    # Act
    response = client.post("/internal/sync", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 422
    dados = response.json()
    assert dados["erro"] is True
    assert "Os dados enviados são inválidos" in dados["mensagem"]
    # Verifica que detalhes de erro estão na resposta
    assert len(dados["detalhes"]) > 0

@pytest.fixture
def mock_db_session(mocker):
    # Mockando a dependência do banco de dados para evitar gravar no DB real
    mock_session = mocker.MagicMock()
    # Mock da query(OportunidadeDB).filter(...).first()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = None  # Simula que a vaga não existe
    
    return mock_session

def test_sync_data_vaga_qualificada_salva_com_sucesso(mocker, mock_db_session):
    # Arrange
    headers = {
        "Content-Type": "application/json",
        "X-Sync-Key": settings.sync_api_key
    }
    payload = [
        {
            "titulo": "Vaga Completa",
            "origem": "UFC",
            "tipo": "Bolsa",
            "link": "http://link.com/vaga",
            "data_inicio": "2026-06-20T00:00:00",
            "data_fim": "2026-12-20T00:00:00",
            "remuneracao": 500.0,
            "vagas": 1,
            "resultados": []
        }
    ]
    
    # Para simular o banco com app client de forma isolada, faremos o override da dependência real
    from app.db.database import get_db
    app.dependency_overrides[get_db] = lambda: mock_db_session

    # Act
    response = client.post("/internal/sync", json=payload, headers=headers)
    
    # Limpa dependências
    app.dependency_overrides = {}

    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["status"] == "sucesso"
    assert dados["oportunidades_recebidas"] == 1
    assert dados["oportunidades_descartadas"] == 0
    assert dados["oportunidades_novas"] == 1
    
    # Verifica que db.add e db.commit foram chamados
    assert mock_db_session.add.call_count == 1
    mock_db_session.commit.assert_called_once()
