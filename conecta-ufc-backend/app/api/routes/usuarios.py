from fastapi import APIRouter, Depends, status

from app.core.auth import get_current_user_claims
from app.schemas.auth import UsuarioAutenticado
from app.schemas.esquecisenha import EsqueciSenhaRequest
from app.schemas.usuario import (
    LoginRequest,
    LoginResponse,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.services.keycloak_service import (
    atualizar_usuario_keycloak,
    criar_usuario_keycloak,
    login_keycloak,
    obter_usuario_keycloak,
    recuperar_senha_keycloak,
)


router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: UsuarioCreate):
    usuario_id = criar_usuario_keycloak(usuario)

    return UsuarioResponse(
        id=usuario_id,
        email=usuario.email,
        nome=usuario.nome,
        curso=usuario.curso,
        oportunidades=usuario.oportunidades,
    )


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest):
    return login_keycloak(login_data)


@router.get("/me", response_model=UsuarioAutenticado)
def obter_usuario_logado(claims: dict = Depends(get_current_user_claims)):
    return obter_usuario_keycloak(claims["sub"])


@router.put("/me", response_model=UsuarioAutenticado)
def atualizar_usuario(
    usuario: UsuarioUpdate,
    claims: dict = Depends(get_current_user_claims),
):
    return atualizar_usuario_keycloak(claims["sub"], usuario)


#Atualmente o esqueci minha senha não tem servidor SMTP, então está enviando para o Malphite, veja o readme em caso de dúvidas sabrina-sama
@router.post("/esqueci-senha", status_code=status.HTTP_200_OK)
def recuperar_senha(request: EsqueciSenhaRequest):
    recuperar_senha_keycloak(request)
    return {
          "message": "Se o email estiver cadastrado, um link de recuperação foi enviado."
      }
