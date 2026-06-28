import pytest
from app.core.auth import get_current_user_claims
from app.main import app

@pytest.fixture
def mock_keycloak(monkeypatch):
    import app.services.keycloak_service as kc
    
    def mock_criar_usuario(usuario):
        if usuario.email == "duplicado@teste.com":
            from fastapi import HTTPException
            raise HTTPException(status_code=409, detail="Usuario ja cadastrado com este e-mail")
        return "fake_keycloak_id_123"
        
    def mock_login(login_data):
        if login_data.senha == "senha_errada":
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Email ou senha invalidos")
        return {
            "access_token": "fake_token", 
            "token_type": "bearer",
            "refresh_token": "fake_refresh",
            "expires_in": 3600,
            "refresh_expires_in": 7200
        }
        
    def mock_recuperar_senha(request):
        pass

    def mock_obter_usuario(usuario_id):
        return {
            "sub": usuario_id,
            "email": "usuario@teste.com",
            "preferred_username": "usuario@teste.com",
            "preferencias": ["Bolsa", "Estágio"],
            "nome": "João Silva",
            "curso": "Ciência da Computação",
            "oportunidades": ["Bolsa", "Estágio"],
        }

    import app.api.routes.usuarios as routers_usuarios
    monkeypatch.setattr(routers_usuarios, "criar_usuario_keycloak", mock_criar_usuario)
    monkeypatch.setattr(routers_usuarios, "login_keycloak", mock_login)
    monkeypatch.setattr(routers_usuarios, "obter_usuario_keycloak", mock_obter_usuario)
    monkeypatch.setattr(routers_usuarios, "recuperar_senha_keycloak", mock_recuperar_senha)

def mock_get_current_user_claims():
    return {"sub": "fake_keycloak_id_123", "preferred_username": "usuario@teste.com", "email": "usuario@teste.com"}

@pytest.fixture
def override_auth():
    from app.core.auth import get_current_user_claims
    app.dependency_overrides[get_current_user_claims] = mock_get_current_user_claims
    yield
    app.dependency_overrides.clear()

# --- Testes de Integração para Usuarios ---

def test_integration_usuarios_registro_com_sucesso(client, mock_keycloak):
    payload = {
        "email": "usuario@teste.com",
        "senha": "SenhaForte123",
        "nome": "João",
        "sobrenome": "Silva",
        "curso": "Ciência da Computação",
        "oportunidades": ["Bolsa", "Estágio"]
    }
    
    response = client.post("/usuarios", json=payload)
    
    assert response.status_code == 201
    dados = response.json()
    assert dados["email"] == "usuario@teste.com"
    assert dados["id"] == "fake_keycloak_id_123"

def test_integration_usuarios_registro_email_duplicado_retorna_409(client, mock_keycloak):
    payload = {
        "email": "duplicado@teste.com",
        "senha": "SenhaForte123",
        "nome": "Novo",
        "sobrenome": "Nome",
        "curso": "Engenharia",
        "oportunidades": []
    }
    
    # Act
    response = client.post("/usuarios", json=payload)
    
    # Assert
    assert response.status_code == 409
    assert "Usuario ja cadastrado com este e-mail" in response.json().get("mensagem", response.json().get("detail", ""))

def test_integration_usuarios_login_sucesso_retorna_token(client, mock_keycloak):
    payload = {
        "email": "usuario@teste.com",
        "senha": "SenhaForte123"
    }
    
    # Act
    response = client.post("/usuarios/login", json=payload)
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["access_token"] == "fake_token"
    assert dados["token_type"] == "bearer"

def test_integration_usuarios_login_senha_incorreta_retorna_401(client, mock_keycloak):
    payload = {
        "email": "usuario@teste.com",
        "senha": "senha_errada"
    }
    response = client.post("/usuarios/login", json=payload)
    assert response.status_code == 401
    assert "Email ou senha invalidos" in response.json().get("mensagem", response.json().get("detail", ""))

def test_integration_usuarios_me_retorna_dados_do_usuario_autenticado(client, override_auth, mock_keycloak):
    # Act
    response = client.get("/usuarios/me")
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["email"] == "usuario@teste.com"
    assert dados["sub"] == "fake_keycloak_id_123"
    assert dados["preferencias"] == ["Bolsa", "Estágio"]
    assert dados["nome"] == "João Silva"
    assert dados["curso"] == "Ciência da Computação"
    assert dados["oportunidades"] == ["Bolsa", "Estágio"]

def test_integration_usuarios_esqueci_senha_retorna_sucesso(client, mock_keycloak):
    payload = {"email": "usuario@teste.com"}
    response = client.post("/usuarios/esqueci-senha", json=payload)
    
    assert response.status_code == 200
    assert "recuperação foi enviado" in response.json()["message"]
