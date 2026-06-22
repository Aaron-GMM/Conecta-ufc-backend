import pytest
from app.schemas.favorito import FavoritoCreate, FavoritoResponse

def test_favorito_create_valido():
    fav = FavoritoCreate(oportunidade_id=10)
    assert fav.oportunidade_id == 10

def test_favorito_response_valido():
    fav_resp = FavoritoResponse(id=1, usuario_id="user123", oportunidade_id=10)
    assert fav_resp.id == 1
    assert fav_resp.usuario_id == "user123"
    assert fav_resp.oportunidade_id == 10
