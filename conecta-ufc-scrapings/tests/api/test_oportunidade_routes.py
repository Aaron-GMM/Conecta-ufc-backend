import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.oportunidade import OportunidadeDB
from app.db.database import get_db

client = TestClient(app)

def test_listar_oportunidades_paginadas_retorna_dados_e_meta():
    mock_db = MagicMock()
    
    mock_query = mock_db.query.return_value
    mock_query.count.return_value = 1
    
    vaga = OportunidadeDB(
        id=1, titulo="Op", origem="UFC", tipo="Bolsa", link="link",
        resultados=[]
    )
    
    mock_options = mock_query.options.return_value
    mock_offset = mock_options.offset.return_value
    mock_limit = mock_offset.limit.return_value
    mock_limit.all.return_value = [vaga]
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    response = client.get("/api/oportunidades/?page=1&size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["meta"]["total_elements"] == 1
    assert data["meta"]["total_pages"] == 1
    assert data["meta"]["has_next"] is False
    assert data["meta"]["has_previous"] is False
    
    app.dependency_overrides.clear()
