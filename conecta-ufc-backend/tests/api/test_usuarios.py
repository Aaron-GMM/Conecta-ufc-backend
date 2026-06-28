import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.core.auth import get_current_user_claims

client = TestClient(app)

# --- Testes para criar_usuario ---

@patch("app.api.routes.usuarios.criar_usuario_keycloak")
def test_criar_usuario_dados_validos_retorna_201_com_dados_mapeados(mock_criar_usuario_keycloak):
    # Arrange
    mock_criar_usuario_keycloak.return_value = "new_uuid_123"
    payload = {
        "nome": "João da Silva",
        "email": "joao@ufc.br",
        "senha": "SenhaForte123!",
        "curso": "Computação",
        "oportunidades": ["Bolsa", "Estágio"]
    }
    
    # Act
    response = client.post("/usuarios", json=payload)
    
    # Assert
    assert response.status_code == 201
    dados = response.json()
    assert dados["id"] == "new_uuid_123"
    assert dados["email"] == "joao@ufc.br"
    assert dados["nome"] == "João da Silva"
    assert dados["curso"] == "Computação"
    assert "Bolsa" in dados["oportunidades"]

@patch("app.api.routes.usuarios.criar_usuario_keycloak")
def test_criar_usuario_dados_invalidos_retorna_422(mock_criar_usuario_keycloak):
    # Arrange
    # Faltando email e senha
    payload = {
        "nome": "Incompleto"
    }
    
    # Act
    response = client.post("/usuarios", json=payload)
    
    # Assert
    assert response.status_code == 422
    dados = response.json()
    assert dados["erro"] is True
    assert len(dados["detalhes"]) > 0

# --- Testes para login ---

@patch("app.api.routes.usuarios.login_keycloak")
def test_login_credenciais_corretas_retorna_200_com_tokens(mock_login_keycloak):
    # Arrange
    tokens_mock = {
        "access_token": "acc_token",
        "refresh_token": "ref_token",
        "expires_in": 3600,
        "refresh_expires_in": 7200,
        "token_type": "Bearer"
    }
    mock_login_keycloak.return_value = tokens_mock
    payload = {
        "email": "teste@ufc.br",
        "senha": "123"
    }
    
    # Act
    response = client.post("/usuarios/login", json=payload)
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["access_token"] == "acc_token"
    assert dados["token_type"] == "Bearer"

# --- Testes para obter_usuario_logado ---

@patch("app.api.routes.usuarios.obter_usuario_keycloak")
def test_obter_usuario_logado_token_valido_retorna_perfil(mock_obter_usuario):
    # Arrange
    mock_claims = {
        "sub": "uuid-1234",
        "email": "user@ufc.br",
        "preferred_username": "user123"
    }
    mock_obter_usuario.return_value = {
        "sub": "uuid-1234",
        "email": "user@ufc.br",
        "preferred_username": "user@ufc.br",
        "preferencias": ["Bolsa", "Estágio"],
        "nome": "Usuário Teste",
        "curso": "Computação",
        "oportunidades": ["Bolsa", "Estágio"],
    }
    
    # Fazendo override da dependência
    app.dependency_overrides[get_current_user_claims] = lambda: mock_claims
    
    # Act
    response = client.get("/usuarios/me")
    
    # Limpando override
    app.dependency_overrides = {}
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["sub"] == "uuid-1234"
    assert dados["email"] == "user@ufc.br"
    assert dados["preferred_username"] == "user@ufc.br"
    assert dados["preferencias"] == ["Bolsa", "Estágio"]
    assert dados["nome"] == "Usuário Teste"
    assert dados["curso"] == "Computação"
    assert dados["oportunidades"] == ["Bolsa", "Estágio"]
    mock_obter_usuario.assert_called_once_with("uuid-1234")

def test_obter_usuario_logado_sem_token_retorna_401():
    # Arrange
    # Sem override, vai passar pelo middleware real
    
    # Act
    response = client.get("/usuarios/me")
    
    # Assert
    assert response.status_code == 401
    assert "Token Bearer nao informado" in response.json()["mensagem"]


# --- Testes para atualizar_usuario ---

@patch("app.api.routes.usuarios.atualizar_usuario_keycloak")
def test_atualizar_usuario_retorna_dados_atualizados(mock_atualizar):
    app.dependency_overrides[get_current_user_claims] = lambda: {"sub": "uuid-1234"}
    mock_atualizar.return_value = {
        "sub": "uuid-1234",
        "email": "novo@ufc.br",
        "preferred_username": "antigo@ufc.br",
        "nome": "Novo Nome",
        "curso": "Computação",
        "preferencias": ["Estágio", "Bolsa"],
        "oportunidades": ["Estágio", "Bolsa"],
    }

    response = client.put(
        "/usuarios/me",
        json={
            "email": "novo@ufc.br",
            "nome": "Novo Nome",
            "preferencias": ["Estágio", "Bolsa"],
        },
    )
    app.dependency_overrides = {}

    assert response.status_code == 200
    assert response.json()["preferencias"] == ["Estágio", "Bolsa"]
    usuario_id, atualizacao = mock_atualizar.call_args.args
    assert usuario_id == "uuid-1234"
    assert atualizacao.nome == "Novo Nome"


def test_atualizar_usuario_sem_campos_retorna_422():
    app.dependency_overrides[get_current_user_claims] = lambda: {"sub": "uuid-1234"}

    response = client.put("/usuarios/me", json={})
    app.dependency_overrides = {}

    assert response.status_code == 422


def test_atualizar_usuario_sem_token_retorna_401():
    response = client.put("/usuarios/me", json={"nome": "Novo Nome"})

    assert response.status_code == 401


# --- Testes para recuperar_senha ---

@patch("app.api.routes.usuarios.recuperar_senha_keycloak")
def test_recuperar_senha_chama_servico_e_retorna_mensagem(mock_recuperar):
    # Arrange
    payload = {"email": "esqueci@ufc.br"}
    
    # Act
    response = client.post("/usuarios/esqueci-senha", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert "um link de recuperação foi enviado" in response.json()["message"]
    mock_recuperar.assert_called_once()
