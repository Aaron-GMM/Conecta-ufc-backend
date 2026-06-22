import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import (
    _issuer_url,
    _token_pertence_ao_cliente,
    validar_token_keycloak,
    get_current_user_claims,
    get_current_user_id
)
from app.core.config import settings

# --- Testes para _issuer_url ---

def test_issuer_url_settings_tem_issuer_retorna_issuer():
    # Arrange
    with patch("app.core.auth.settings.keycloak_issuer_url", "http://issuer.com/"):
        # Act
        url = _issuer_url()
        # Assert
        assert url == "http://issuer.com"

def test_issuer_url_settings_sem_issuer_retorna_fallback():
    # Arrange
    with patch("app.core.auth.settings.keycloak_issuer_url", None):
        with patch("app.core.auth.settings.keycloak_server_url", "http://server.com/"):
            with patch("app.core.auth.settings.keycloak_realm", "my_realm"):
                # Act
                url = _issuer_url()
                # Assert
                assert url == "http://server.com/realms/my_realm"

# --- Testes para _token_pertence_ao_cliente ---

def test_token_pertence_ao_cliente_cliente_no_azp_retorna_true():
    # Arrange
    payload = {"azp": settings.keycloak_client_id}
    
    # Act
    resultado = _token_pertence_ao_cliente(payload)
    
    # Assert
    assert resultado is True

def test_token_pertence_ao_cliente_cliente_no_aud_array_retorna_true():
    # Arrange
    payload = {"aud": ["outro_cliente", settings.keycloak_client_id]}
    
    # Act
    resultado = _token_pertence_ao_cliente(payload)
    
    # Assert
    assert resultado is True

def test_token_pertence_ao_cliente_cliente_no_aud_string_retorna_true():
    # Arrange
    payload = {"aud": settings.keycloak_client_id}
    
    # Act
    resultado = _token_pertence_ao_cliente(payload)
    
    # Assert
    assert resultado is True

def test_token_pertence_ao_cliente_cliente_nao_presente_retorna_false():
    # Arrange
    payload = {"azp": "cliente_desconhecido", "aud": ["cliente1"]}
    
    # Act
    resultado = _token_pertence_ao_cliente(payload)
    
    # Assert
    assert resultado is False

# --- Testes para validar_token_keycloak ---

@patch("app.core.auth._criar_openid_keycloak")
@patch("app.core.auth._token_pertence_ao_cliente")
def test_validar_token_keycloak_token_valido_retorna_payload(mock_pertence, mock_criar_openid):
    # Arrange
    mock_openid = MagicMock()
    mock_payload = {"sub": "123", "azp": settings.keycloak_client_id}
    mock_openid.decode_token.return_value = mock_payload
    mock_criar_openid.return_value = mock_openid
    mock_pertence.return_value = True
    
    # Act
    resultado = validar_token_keycloak("token_valido")
    
    # Assert
    assert resultado == mock_payload
    mock_openid.decode_token.assert_called_once()
    mock_pertence.assert_called_once_with(mock_payload)

@patch("app.core.auth._criar_openid_keycloak")
def test_validar_token_keycloak_token_invalido_lanca_excecao(mock_criar_openid):
    # Arrange
    mock_openid = MagicMock()
    mock_openid.decode_token.side_effect = Exception("Invalid token")
    mock_criar_openid.return_value = mock_openid
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        validar_token_keycloak("token_invalido")
        
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token de acesso invalido" in exc_info.value.detail

@patch("app.core.auth._criar_openid_keycloak")
@patch("app.core.auth._token_pertence_ao_cliente")
def test_validar_token_keycloak_cliente_errado_lanca_excecao(mock_pertence, mock_criar_openid):
    # Arrange
    mock_openid = MagicMock()
    mock_payload = {"sub": "123", "azp": "hacker_client"}
    mock_openid.decode_token.return_value = mock_payload
    mock_criar_openid.return_value = mock_openid
    mock_pertence.return_value = False
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        validar_token_keycloak("token_cliente_errado")
        
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "cliente invalido" in exc_info.value.detail

# --- Testes para get_current_user_claims ---

@patch("app.core.auth.validar_token_keycloak")
def test_get_current_user_claims_credenciais_validas_retorna_payload(mock_validar):
    # Arrange
    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="meu_token")
    mock_payload = {"sub": "user_1"}
    mock_validar.return_value = mock_payload
    
    # Act
    resultado = get_current_user_claims(credentials=cred)
    
    # Assert
    assert resultado == mock_payload
    mock_validar.assert_called_once_with("meu_token")

def test_get_current_user_claims_credenciais_nulas_lanca_excecao():
    # Arrange
    cred = None
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_claims(credentials=cred)
        
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token Bearer nao informado" in exc_info.value.detail

def test_get_current_user_claims_scheme_invalido_lanca_excecao():
    # Arrange
    cred = HTTPAuthorizationCredentials(scheme="Basic", credentials="abc")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_claims(credentials=cred)
        
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token Bearer nao informado" in exc_info.value.detail

# --- Testes para get_current_user_id ---

def test_get_current_user_id_claims_com_sub_retorna_id():
    # Arrange
    claims = {"sub": "user_id_123"}
    
    # Act
    resultado = get_current_user_id(claims=claims)
    
    # Assert
    assert resultado == "user_id_123"

def test_get_current_user_id_claims_sem_sub_lanca_excecao():
    # Arrange
    claims = {"azp": "client"}
    
    # Act & Assert
    with pytest.raises(KeyError):
        get_current_user_id(claims=claims)
