import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakError
from app.services.keycloak_service import (
    _criar_admin_keycloak,
    atualizar_usuario_keycloak,
    criar_usuario_keycloak,
    login_keycloak,
    obter_usuario_keycloak,
    recuperar_senha_keycloak
)
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, LoginRequest
from app.schemas.esquecisenha import EsqueciSenhaRequest

# --- Testes para _criar_admin_keycloak ---

@patch("app.services.keycloak_service.settings.keycloak_client_secret", None)
def test_criar_admin_keycloak_sem_secret_lanca_excecao():
    # Arrange / Act / Assert
    with pytest.raises(HTTPException) as exc_info:
        _criar_admin_keycloak()
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "KEYCLOAK_CLIENT_SECRET" in exc_info.value.detail

@patch("app.services.keycloak_service.KeycloakAdmin")
def test_criar_admin_keycloak_com_secret_retorna_instancia(mock_keycloak_admin):
    # Arrange
    with patch("app.services.keycloak_service.settings.keycloak_client_secret", "secret123"):
        mock_instance = MagicMock()
        mock_keycloak_admin.return_value = mock_instance
        
        # Act
        resultado = _criar_admin_keycloak()
        
        # Assert
        assert resultado == mock_instance
        mock_keycloak_admin.assert_called_once()

# --- Testes para criar_usuario_keycloak ---

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_criar_usuario_keycloak_sucesso_retorna_id(mock_criar_admin):
    # Arrange
    usuario = UsuarioCreate(
        nome="João Silva",
        email="joao@teste.com",
        senha="senha forte",
        curso="Computação",
        oportunidades=["Bolsa"]
    )
    mock_admin_instance = MagicMock()
    mock_admin_instance.create_user.return_value = "new_user_id"
    mock_criar_admin.return_value = mock_admin_instance
    
    # Act
    resultado = criar_usuario_keycloak(usuario)
    
    # Assert
    assert resultado == "new_user_id"
    mock_admin_instance.create_user.assert_called_once()
    payload_enviado = mock_admin_instance.create_user.call_args[0][0]
    assert payload_enviado["username"] == "joao@teste.com"
    assert payload_enviado["firstName"] == "João"
    assert payload_enviado["lastName"] == "Silva"

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_criar_usuario_keycloak_email_duplicado_lanca_409(mock_criar_admin):
    # Arrange
    usuario = UsuarioCreate(
        nome="Maria Silva",
        email="maria@teste.com",
        senha="senha_valida",
        curso="Engenharia",
        oportunidades=[]
    )
    mock_admin_instance = MagicMock()
    mock_admin_instance.create_user.side_effect = KeycloakError("Error 409: Conflict")
    mock_criar_admin.return_value = mock_admin_instance
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        criar_usuario_keycloak(usuario)
        
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "Usuario ja cadastrado" in exc_info.value.detail

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_criar_usuario_keycloak_erro_generico_lanca_400(mock_criar_admin):
    # Arrange
    usuario = UsuarioCreate(
        nome="Maria",
        email="maria@teste.com",
        senha="senha_valida",
        curso="Eng",
        oportunidades=[]
    )
    mock_admin_instance = MagicMock()
    mock_admin_instance.create_user.side_effect = KeycloakError("Outro erro do Keycloak")
    mock_criar_admin.return_value = mock_admin_instance
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        criar_usuario_keycloak(usuario)
        
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


# --- Testes para obter_usuario_keycloak ---

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_obter_usuario_keycloak_retorna_perfil_completo(mock_criar_admin):
    mock_admin = MagicMock()
    mock_admin.get_user.return_value = {
        "id": "user-1",
        "email": "usuario@teste.com",
        "username": "usuario@teste.com",
        "firstName": "João",
        "lastName": "Silva",
        "attributes": {
            "curso": ["Computação"],
            "oportunidades": ["Bolsa", "Estágio"],
        },
    }
    mock_criar_admin.return_value = mock_admin

    resultado = obter_usuario_keycloak("user-1")

    assert resultado == {
        "sub": "user-1",
        "email": "usuario@teste.com",
        "preferred_username": "usuario@teste.com",
        "nome": "João Silva",
        "curso": "Computação",
        "oportunidades": ["Bolsa", "Estágio"],
    }


@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_obter_usuario_keycloak_nome_repetido_retorna_nome_unico(mock_criar_admin):
    mock_admin = MagicMock()
    mock_admin.get_user.return_value = {
        "id": "user-1",
        "email": "maria@teste.com",
        "username": "maria@teste.com",
        "firstName": "Maria",
        "lastName": "Maria",
        "attributes": {},
    }
    mock_criar_admin.return_value = mock_admin

    resultado = obter_usuario_keycloak("user-1")

    assert resultado["nome"] == "Maria"
    assert resultado["curso"] == ""
    assert resultado["oportunidades"] == []


# --- Testes para atualizar_usuario_keycloak ---

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_atualizar_usuario_keycloak_atualiza_campos_e_preserva_atributos(mock_criar_admin):
    mock_admin = MagicMock()
    mock_admin.get_user.side_effect = [
        {"attributes": {"curso": ["Computação"]}},
        {
            "id": "user-1",
            "email": "novo@teste.com",
            "username": "antigo@teste.com",
            "firstName": "João",
            "lastName": "Silva",
            "attributes": {
                "curso": ["Computação"],
                "oportunidades": ["Bolsa", "Estágio"],
            },
        },
    ]
    mock_criar_admin.return_value = mock_admin
    atualizacao = UsuarioUpdate(
        email="novo@teste.com",
        nome="João Silva",
        curso="Engenharia de Software",
        oportunidades=["Bolsa", "Estágio"],
    )

    resultado = atualizar_usuario_keycloak("user-1", atualizacao)

    payload = mock_admin.update_user.call_args.args[1]
    assert payload["email"] == "novo@teste.com"
    assert payload["emailVerified"] is False
    assert payload["firstName"] == "João"
    assert payload["lastName"] == "Silva"
    assert payload["attributes"]["curso"] == ["Engenharia de Software"]
    assert payload["attributes"]["oportunidades"] == ["Bolsa", "Estágio"]
    assert resultado["nome"] == "João Silva"
    assert resultado["oportunidades"] == ["Bolsa", "Estágio"]
    assert resultado["sub"] == "user-1"


@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_atualizar_usuario_keycloak_email_duplicado_retorna_409(mock_criar_admin):
    mock_admin = MagicMock()
    mock_admin.get_user.return_value = {"attributes": {}}
    erro = KeycloakError("Error 409: Conflict")
    erro.response_code = 409
    mock_admin.update_user.side_effect = erro
    mock_criar_admin.return_value = mock_admin

    with pytest.raises(HTTPException) as exc_info:
        atualizar_usuario_keycloak(
            "user-1",
            UsuarioUpdate(email="duplicado@teste.com"),
        )

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_atualizar_usuario_keycloak_nome_unico_atende_requisito_do_realm(mock_criar_admin):
    mock_admin = MagicMock()
    mock_admin.get_user.side_effect = [
        {"attributes": {}},
        {
            "id": "user-1",
            "email": "maria@teste.com",
            "username": "maria@teste.com",
            "firstName": "Maria",
            "lastName": "Maria",
            "attributes": {},
        },
    ]
    mock_criar_admin.return_value = mock_admin

    resultado = atualizar_usuario_keycloak(
        "user-1",
        UsuarioUpdate(nome="Maria"),
    )

    payload = mock_admin.update_user.call_args.args[1]
    assert payload["firstName"] == "Maria"
    assert payload["lastName"] == "Maria"
    assert resultado["nome"] == "Maria"


# --- Testes para login_keycloak ---

@patch("app.services.keycloak_service.KeycloakOpenID")
def test_login_keycloak_credenciais_validas_retorna_tokens(mock_keycloak_openid):
    # Arrange
    login = LoginRequest(email="user@teste.com", senha="123")
    mock_openid_instance = MagicMock()
    mock_tokens = {
        "access_token": "acc_tok",
        "refresh_token": "ref_tok",
        "expires_in": 3600,
        "refresh_expires_in": 7200,
        "token_type": "Bearer"
    }
    mock_openid_instance.token.return_value = mock_tokens
    mock_keycloak_openid.return_value = mock_openid_instance
    
    # Act
    resultado = login_keycloak(login)
    
    # Assert
    assert resultado == mock_tokens
    mock_openid_instance.token.assert_called_once_with("user@teste.com", "123")

@patch("app.services.keycloak_service.KeycloakOpenID")
def test_login_keycloak_credenciais_invalidas_lanca_401(mock_keycloak_openid):
    # Arrange
    login = LoginRequest(email="user@teste.com", senha="bad")
    mock_openid_instance = MagicMock()
    mock_openid_instance.token.side_effect = KeycloakError("Invalid creds")
    mock_keycloak_openid.return_value = mock_openid_instance
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        login_keycloak(login)
        
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

# --- Testes para recuperar_senha_keycloak ---

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_recuperar_senha_keycloak_email_nao_encontrado_nao_faz_nada(mock_criar_admin):
    # Arrange
    req = EsqueciSenhaRequest(email="ghost@teste.com")
    mock_admin_instance = MagicMock()
    mock_admin_instance.get_user_id.return_value = None
    mock_criar_admin.return_value = mock_admin_instance
    
    # Act
    recuperar_senha_keycloak(req)
    
    # Assert
    mock_admin_instance.get_user_id.assert_called_once_with("ghost@teste.com")
    mock_admin_instance.send_update_account.assert_not_called()

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_recuperar_senha_keycloak_email_encontrado_envia_update(mock_criar_admin):
    # Arrange
    req = EsqueciSenhaRequest(email="real@teste.com")
    mock_admin_instance = MagicMock()
    mock_admin_instance.get_user_id.return_value = "user_id_1"
    mock_criar_admin.return_value = mock_admin_instance
    
    # Act
    recuperar_senha_keycloak(req)
    
    # Assert
    mock_admin_instance.get_user_id.assert_called_once_with("real@teste.com")
    mock_admin_instance.send_update_account.assert_called_once()
    args, kwargs = mock_admin_instance.send_update_account.call_args
    assert args[0] == "user_id_1"
    assert "UPDATE_PASSWORD" in kwargs["payload"]

@patch("app.services.keycloak_service._criar_admin_keycloak")
def test_recuperar_senha_keycloak_erro_no_keycloak_lanca_400(mock_criar_admin):
    # Arrange
    req = EsqueciSenhaRequest(email="real@teste.com")
    mock_admin_instance = MagicMock()
    mock_admin_instance.get_user_id.return_value = "user_id_1"
    mock_admin_instance.send_update_account.side_effect = KeycloakError("Fail")
    mock_criar_admin.return_value = mock_admin_instance
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        recuperar_senha_keycloak(req)
        
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
