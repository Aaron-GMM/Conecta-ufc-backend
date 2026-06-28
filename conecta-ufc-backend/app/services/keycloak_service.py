import logging

from fastapi import HTTPException, status
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakError

from app.core.config import settings
from app.schemas.esquecisenha import EsqueciSenhaRequest
from app.schemas.usuario import LoginRequest, UsuarioCreate, UsuarioUpdate


logger = logging.getLogger(__name__)


def _mapear_perfil_usuario(usuario: dict) -> dict:
    atributos = usuario.get("attributes") or {}
    oportunidades = atributos.get("oportunidades", [])
    cursos = atributos.get("curso", [])
    primeiro_nome = usuario.get("firstName")
    sobrenome = usuario.get("lastName")
    partes_nome = [primeiro_nome]
    if sobrenome and sobrenome != primeiro_nome:
        partes_nome.append(sobrenome)

    return {
        "sub": usuario["id"],
        "email": usuario.get("email"),
        "preferred_username": usuario.get("username"),
        "nome": " ".join(parte for parte in partes_nome if parte),
        "curso": cursos[0] if cursos else "",
        "oportunidades": oportunidades,
    }


def _criar_admin_keycloak() -> KeycloakAdmin:
    if not settings.keycloak_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KEYCLOAK_CLIENT_SECRET nao configurado",
        )

    return KeycloakAdmin(
        server_url=settings.keycloak_server_url,
        realm_name=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        client_secret_key=settings.keycloak_client_secret,
        verify=True,
    )


def criar_usuario_keycloak(usuario: UsuarioCreate) -> str:
    partes_nome = usuario.nome.strip().split(maxsplit=1)
    primeiro_nome = partes_nome[0]
    sobrenome = partes_nome[1] if len(partes_nome) > 1 else partes_nome[0]

    keycloak_admin = _criar_admin_keycloak()

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
        error_msg = str(exc)
        if "409" in error_msg or (hasattr(exc, 'response_code') and exc.response_code == 409):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Usuario ja cadastrado com este e-mail",
            ) from exc
        
        logger.exception(f"Falha ao criar usuario no Keycloak: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel criar o usuario no Keycloak. Verifique os dados.",
        ) from exc


def obter_usuario_keycloak(usuario_id: str) -> dict:
    keycloak_admin = _criar_admin_keycloak()

    try:
        usuario = keycloak_admin.get_user(usuario_id)
    except KeycloakError as exc:
        logger.exception("Falha ao obter usuario no Keycloak")
        codigo = getattr(exc, "response_code", None)
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if codigo == status.HTTP_404_NOT_FOUND
                else status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Usuario nao encontrado."
                if codigo == status.HTTP_404_NOT_FOUND
                else "Nao foi possivel consultar o provedor de identidade."
            ),
        ) from exc

    return _mapear_perfil_usuario(usuario)


def atualizar_usuario_keycloak(usuario_id: str, usuario: UsuarioUpdate) -> dict:
    keycloak_admin = _criar_admin_keycloak()

    try:
        usuario_atual = keycloak_admin.get_user(usuario_id)
        payload = {}

        if usuario.email is not None:
            novo_email = str(usuario.email)
            payload.update(
                {
                    "email": novo_email,
                    "emailVerified": False,
                }
            )

        if usuario.nome is not None:
            partes_nome = usuario.nome.strip().split(maxsplit=1)
            payload["firstName"] = partes_nome[0]
            payload["lastName"] = (
                partes_nome[1] if len(partes_nome) > 1 else partes_nome[0]
            )

        if usuario.curso is not None or usuario.oportunidades is not None:
            atributos = dict(usuario_atual.get("attributes") or {})
            if usuario.curso is not None:
                atributos["curso"] = [usuario.curso]
            if usuario.oportunidades is not None:
                atributos["oportunidades"] = usuario.oportunidades
            payload["attributes"] = atributos

        keycloak_admin.update_user(usuario_id, payload)
        usuario_atualizado = keycloak_admin.get_user(usuario_id)
    except KeycloakError as exc:
        if getattr(exc, "response_code", None) == status.HTTP_409_CONFLICT or "409" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Usuario ja cadastrado com este e-mail",
            ) from exc

        logger.exception("Falha ao atualizar usuario no Keycloak")
        codigo = getattr(exc, "response_code", None)
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
                if codigo == status.HTTP_404_NOT_FOUND
                else status.HTTP_502_BAD_GATEWAY
            ),
            detail=(
                "Usuario nao encontrado."
                if codigo == status.HTTP_404_NOT_FOUND
                else "Nao foi possivel atualizar o usuario no provedor de identidade."
            ),
        ) from exc

    return _mapear_perfil_usuario(usuario_atualizado)


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
        logger.exception("Falha ao autenticar usuario no Keycloak")
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


def recuperar_senha_keycloak(esqueci_senha: EsqueciSenhaRequest) -> None:
    keycloak_admin = _criar_admin_keycloak()

    try:
        user_id = keycloak_admin.get_user_id(esqueci_senha.email)
        if not user_id:
            logger.info(
                "Pedido de recuperacao de senha para email nao encontrado no Keycloak"
            )
            return

        keycloak_admin.send_update_account(
            user_id,
            payload=["UPDATE_PASSWORD"],
            client_id=settings.keycloak_frontend_client_id,
            redirect_uri=settings.frontend_login_url,
        )
    except KeycloakError as exc:
        logger.exception("Falha ao enviar email de recuperacao de senha pelo Keycloak")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel enviar o email de recuperacao de senha.",
        ) from exc
