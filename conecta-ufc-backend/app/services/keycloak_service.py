from fastapi import HTTPException, status
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakError

from app.core.config import settings
from app.schemas.usuario import LoginRequest, UsuarioCreate


def criar_usuario_keycloak(usuario: UsuarioCreate) -> str:
    if not settings.keycloak_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KEYCLOAK_CLIENT_SECRET nao configurado",
        )

    partes_nome = usuario.nome.strip().split(maxsplit=1)
    primeiro_nome = partes_nome[0]
    sobrenome = partes_nome[1] if len(partes_nome) > 1 else partes_nome[0]

    keycloak_admin = KeycloakAdmin(
        server_url=settings.keycloak_server_url,
        realm_name=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        client_secret_key=settings.keycloak_client_secret,
        verify=True,
    )

    payload = {
        "username": usuario.email,
        "email": usuario.email,
        "firstName": primeiro_nome,
        "lastName": sobrenome,
        "enabled": True,
        "emailVerified": True,
        "requiredActions": [],
        "attributes": {
            "curso": [usuario.curso],
            "oportunidades": usuario.oportunidades,
        },
        "credentials": [
            {
                "type": "password",
                "value": usuario.senha,
                "temporary": False,
            }
        ],
    }

    try:
        return keycloak_admin.create_user(payload)
    except KeycloakError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel criar o usuario no Keycloak",
        ) from exc


def login_keycloak(login: LoginRequest) -> dict:
    keycloak_openid = KeycloakOpenID(
        server_url=settings.keycloak_server_url,
        realm_name=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        client_secret_key=settings.keycloak_client_secret,
    )

    try:
        token = keycloak_openid.token(login.email, login.senha)
    except KeycloakError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha invalidos",
        ) from exc

    return {
        "access_token": token["access_token"],
        "refresh_token": token["refresh_token"],
        "expires_in": token["expires_in"],
        "refresh_expires_in": token["refresh_expires_in"],
        "token_type": token["token_type"],
    }
