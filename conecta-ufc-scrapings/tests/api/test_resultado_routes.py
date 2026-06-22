import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.oportunidade import ResultadoDB
from app.db.database import get_db

client = TestClient(app)

def test_listar_resultados_com_busca_retorna_lista():
    mock_db = MagicMock()
    
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.count.return_value = 1
    
    res = ResultadoDB(id=1, titulo="Resultado Teste", link="link", oportunidade_id=1)
    mock_filter.offset.return_value.limit.return_value.all.return_value = [res]
    
    response = client.get("/api/resultados/?busca=Teste")
    
    assert response.status_code == 200
    assert response.json()["meta"]["total_elements"] == 1
    assert len(response.json()["data"]) == 1
    
    app.dependency_overrides.clear()

def test_obter_resultado_sucesso_retorna_item():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    
    res = ResultadoDB(id=1, titulo="Res", link="l", oportunidade_id=1)
    mock_db.query.return_value.filter.return_value.first.return_value = res
    
    response = client.get("/api/resultados/1")
    assert response.status_code == 200
    assert response.json()["titulo"] == "Res"
    
    app.dependency_overrides.clear()

def test_obter_resultado_falha_retorna_404():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    response = client.get("/api/resultados/999")
    assert response.status_code == 404
    
    app.dependency_overrides.clear()
