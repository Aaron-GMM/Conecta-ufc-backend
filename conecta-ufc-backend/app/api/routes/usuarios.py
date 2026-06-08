from fastapi import APIRouter, status

from app.schemas.usuario import LoginRequest, LoginResponse, UsuarioCreate, UsuarioResponse
from app.services.keycloak_service import criar_usuario_keycloak, login_keycloak


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
