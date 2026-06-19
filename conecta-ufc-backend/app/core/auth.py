import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from keycloak import KeycloakOpenID

from app.core.config import settings


logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def _criar_openid_keycloak() -> KeycloakOpenID:
    return KeycloakOpenID(
        server_url=settings.keycloak_server_url,
        realm_name=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        client_secret_key=settings.keycloak_client_secret,
        verify=True,
    )


def _issuer_url() -> str:
    if settings.keycloak_issuer_url:
        return settings.keycloak_issuer_url.rstrip('/')
    return f"{settings.keycloak_server_url.rstrip('/')}/realms/{settings.keycloak_realm}"


def _token_pertence_ao_cliente(payload: dict) -> bool:
    audiences = payload.get("aud", [])
    if isinstance(audiences, str):
        audiences = [audiences]

    authorized_party = payload.get("azp")
    return (
        authorized_party == settings.keycloak_client_id
        or settings.keycloak_client_id in audiences
    )


def validar_token_keycloak(token: str) -> dict:
    keycloak_openid = _criar_openid_keycloak()

    try:
        payload = keycloak_openid.decode_token(
            token,
            validate=True,
            check_claims={"iss": _issuer_url()},
        )
    except Exception as exc:
        logger.exception("Falha ao validar token de acesso no Keycloak")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso invalido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if not _token_pertence_ao_cliente(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token emitido para cliente invalido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer nao informado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return validar_token_keycloak(credentials.credentials)


def get_current_user_id(claims: dict = Depends(get_current_user_claims)) -> str:
    return claims["sub"]
