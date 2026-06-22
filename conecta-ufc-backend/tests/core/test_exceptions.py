import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import configure_error_handlers
from pydantic import BaseModel

# Configurando um app de teste
app = FastAPI()
configure_error_handlers(app)

class DummyModel(BaseModel):
    campo_obrigatorio: str

@app.get("/test_http_exception")
def route_http_exception():
    raise StarletteHTTPException(status_code=403, detail="Acesso negado.")

@app.post("/test_validation_error")
def route_validation_error(payload: DummyModel):
    return payload

@app.get("/test_sqlalchemy_error")
def route_sqlalchemy_error():
    raise SQLAlchemyError("Erro de banco simulado")

@app.get("/test_general_error")
def route_general_error():
    raise Exception("Erro genérico simulado")

client = TestClient(app, raise_server_exceptions=False)

def test_http_exception_handler_retorna_formato_padrao():
    # Act
    response = client.get("/test_http_exception")
    
    # Assert
    assert response.status_code == 403
    dados = response.json()
    assert dados["erro"] is True
    assert dados["mensagem"] == "Acesso negado."
    assert dados["detalhes"] is None

def test_validation_exception_handler_retorna_formato_padrao_com_detalhes():
    # Arrange (enviando payload vazio para acionar RequestValidationError)
    payload = {}
    
    # Act
    response = client.post("/test_validation_error", json=payload)
    
    # Assert
    assert response.status_code == 422
    dados = response.json()
    assert dados["erro"] is True
    assert "Os dados enviados são inválidos" in dados["mensagem"]
    assert isinstance(dados["detalhes"], list)
    assert len(dados["detalhes"]) > 0
    assert dados["detalhes"][0]["campo"] == "campo_obrigatorio"
    assert dados["detalhes"][0]["erro"] == "Field required"

def test_sqlalchemy_exception_handler_retorna_500_oculta_detalhe_banco():
    # Act
    response = client.get("/test_sqlalchemy_error")
    
    # Assert
    assert response.status_code == 500
    dados = response.json()
    assert dados["erro"] is True
    assert "Ocorreu um problema ao acessar o banco de dados" in dados["mensagem"]
    assert dados["detalhes"] is None

def test_general_exception_handler_retorna_500_oculta_detalhe_geral():
    # Act
    response = client.get("/test_general_error")
    
    # Assert
    assert response.status_code == 500
    dados = response.json()
    assert dados["erro"] is True
    assert "Algo deu errado em nossos servidores" in dados["mensagem"]
    assert dados["detalhes"] is None
