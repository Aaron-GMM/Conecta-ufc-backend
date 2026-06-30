import pytest
import uuid
import os
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine, get_db

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine_e2e = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocalE2E = sessionmaker(autocommit=False, autoflush=False, bind=engine_e2e)

@pytest.fixture(scope="module")
def e2e_db_session():
    from app.models.oportunidade import OportunidadeDB, ResultadoDB, FavoritoDB
    Base.metadata.create_all(bind=engine_e2e)
    session = TestingSessionLocalE2E()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_e2e)

@pytest.fixture(scope="module")
def e2e_client(e2e_db_session):
    def override_get_db():
        try:
            yield e2e_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

SYNC_KEY = os.getenv("SYNC_API_KEY", "conecta-ufc-dev-key")

@pytest.fixture(scope="module")
def shared_data():
    return {
        "email": f"e2e_user_{uuid.uuid4().hex[:8]}@teste.com",
        "senha": "SenhaForte123!",
        "token": None,
        "oportunidade_id": None
    }

# ----------------- FLUXO INTERNO (SYNC) -----------------

def test_e2e_flow_sync_falha_sem_chave(e2e_client):
    response = e2e_client.post("/internal/sync", json=[])
    assert response.status_code == 403

def test_e2e_flow_sync_qualidade_dados(e2e_client):
    headers = {"X-Sync-Key": SYNC_KEY}
    payload = [
        {"titulo": "Sem título", "origem": "UFC", "tipo": "Bolsa", "link": "http://e2e"}, # Falha 1: Titulo
        {"titulo": "Valido", "origem": "UFC", "tipo": "Bolsa", "link": ""},               # Falha 2: Sem Link
        {                                                                                 # Falha 3: Sem dados cruciais e url morta
            "titulo": "Vaga Quebrada",
            "origem": "UFC",
            "tipo": "Bolsa",
            "link": "http://localhost:9999/broken",
            "data_inicio": None, "data_fim": None, "remuneracao": None, "vagas": None
        }
    ]
    response = e2e_client.post("/internal/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["oportunidades_descartadas"] == 3

def test_e2e_flow_sync_sucesso_com_resultados(e2e_client, shared_data):
    headers = {"X-Sync-Key": SYNC_KEY}
    payload = [{
        "titulo": "Bolsa de Teste E2E",
        "origem": "UFC",
        "tipo": "Bolsa",
        "link": "http://e2e-link.com/vaga",
        "data_inicio": "2026-06-20T00:00:00",
        "data_fim": "2026-07-20T00:00:00",
        "remuneracao": 1500.0,
        "vagas": 5,
        "resultados": []
    }]
    response = e2e_client.post("/internal/sync", json=payload, headers=headers)
    assert response.status_code == 200

def test_e2e_flow_sync_atualizacao_com_resultados(e2e_client):
    headers = {"X-Sync-Key": SYNC_KEY}
    payload = [{
        "titulo": "Bolsa de Teste E2E",
        "origem": "UFC",
        "tipo": "Bolsa",
        "link": "http://e2e-link.com/vaga", # Mesma vaga
        "data_inicio": "2026-06-20T00:00:00",
        "remuneracao": 1500.0,
        "vagas": 5,
        "resultados": [{"titulo": "Novo Res", "link": "http://res"}]
    }]
    response = e2e_client.post("/internal/sync", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["resultados_novos"] == 1

# ----------------- FLUXO DE USUARIOS -----------------

def test_e2e_flow_registro_sucesso(e2e_client, shared_data):
    payload = {
        "email": shared_data["email"], "senha": shared_data["senha"],
        "nome": "Usuário E2E", "curso": "Engenharia de Software", "oportunidades": []
    }
    response = e2e_client.post("/usuarios", json=payload)
    assert response.status_code == 201

def test_e2e_flow_registro_duplicado(e2e_client, shared_data):
    payload = {
        "email": shared_data["email"], "senha": shared_data["senha"],
        "nome": "Usuário E2E", "curso": "Eng", "oportunidades": []
    }
    response = e2e_client.post("/usuarios", json=payload)
    assert response.status_code == 409

def test_e2e_flow_login_erro_senha(e2e_client, shared_data):
    payload = {"email": shared_data["email"], "senha": "SenhaIncorreta999"}
    response = e2e_client.post("/usuarios/login", json=payload)
    assert response.status_code == 401

def test_e2e_flow_login_sucesso(e2e_client, shared_data):
    payload = {"email": shared_data["email"], "senha": shared_data["senha"]}
    response = e2e_client.post("/usuarios/login", json=payload)
    assert response.status_code == 200
    shared_data["token"] = response.json()["access_token"]

def test_e2e_flow_consulta_token_ausente(e2e_client):
    response = e2e_client.get("/usuarios/me")
    assert response.status_code == 401

def test_e2e_flow_consulta_token_invalido(e2e_client):
    response = e2e_client.get("/usuarios/me", headers={"Authorization": "Bearer tokenfalso"})
    assert response.status_code == 401

def test_e2e_flow_consulta_sucesso(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.get("/usuarios/me", headers=headers)
    assert response.status_code == 200
    dados = response.json()
    assert dados["sub"]
    assert dados["email"] == shared_data["email"]
    assert dados["nome"] == "Usuário E2E"
    assert dados["curso"] == "Engenharia de Software"
    assert dados["oportunidades"] == []
    assert dados["oportunidades"] == []


def test_e2e_flow_atualiza_perfil(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    novo_email = f"atualizado_{shared_data['email']}"
    response = e2e_client.put(
        "/usuarios/me",
        headers=headers,
        json={
            "email": novo_email,
            "nome": "Novo Nome",
            "oportunidades": ["Bolsa", "Estágio"],
        },
    )

    assert response.status_code == 200
    dados = response.json()
    assert dados["email"] == novo_email
    assert dados["nome"] == "Novo Nome"
    assert dados["oportunidades"] == ["Bolsa", "Estágio"]
    assert dados["oportunidades"] == ["Bolsa", "Estágio"]
    shared_data["email"] = novo_email


def test_e2e_flow_login_com_email_atualizado(e2e_client, shared_data):
    response = e2e_client.post(
        "/usuarios/login",
        json={"email": shared_data["email"], "senha": shared_data["senha"]},
    )

    assert response.status_code == 200
    shared_data["token"] = response.json()["access_token"]

# ----------------- FLUXO DE OPORTUNIDADES E FAVORITOS -----------------

def test_e2e_flow_lista_oportunidades_filtros(e2e_client, shared_data):
    response = e2e_client.get("/oportunidades?busca=E2E&origem=UFC&tipo=Bolsa")
    assert response.status_code == 200
    dados = response.json()
    assert dados["meta"]["total_elements"] >= 1
    shared_data["oportunidade_id"] = dados["data"][0]["id"]


def test_e2e_flow_lista_oportunidades_ordenada_a_z(e2e_client):
    response = e2e_client.get(
        "/oportunidades/ordenadas/a-z?origem=UFC&page=1&size=100"
    )

    assert response.status_code == 200
    dados = response.json()
    titulos = [oportunidade["titulo"] for oportunidade in dados["data"]]
    assert titulos == sorted(titulos, key=str.casefold)
    assert dados["meta"]["current_page"] == 1
    assert dados["meta"]["size"] == 100


def test_e2e_flow_lista_oportunidades_mais_recentes(e2e_client):
    response = e2e_client.get(
        "/oportunidades/ordenadas/mais-recentes?origem=UFC&page=1&size=100"
    )

    assert response.status_code == 200
    dados = response.json()
    datas = [
        oportunidade["data_inicio"]
        for oportunidade in dados["data"]
        if oportunidade["data_inicio"] is not None
    ]
    assert datas == sorted(datas, reverse=True)
    assert dados["meta"]["current_page"] == 1
    assert dados["meta"]["size"] == 100

def test_e2e_flow_favoritar_inexistente(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.post("/oportunidades/99999/favoritar", headers=headers)
    assert response.status_code == 404

def test_e2e_flow_favoritar_sucesso(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.post(f"/oportunidades/{shared_data['oportunidade_id']}/favoritar", headers=headers)
    assert response.status_code == 201

def test_e2e_flow_favoritar_duplicado(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.post(f"/oportunidades/{shared_data['oportunidade_id']}/favoritar", headers=headers)
    assert response.status_code == 201
    assert "já está nos favoritos" in response.json()["message"].lower()

def test_e2e_flow_listar_favoritos(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.get("/oportunidades/favoritos", headers=headers)
    assert response.status_code == 200

def test_e2e_flow_remover_favorito_inexistente(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.delete("/oportunidades/99999/favoritar", headers=headers)
    assert response.status_code == 404

def test_e2e_flow_remover_favorito_sucesso(e2e_client, shared_data):
    headers = {"Authorization": f"Bearer {shared_data['token']}"}
    response = e2e_client.delete(f"/oportunidades/{shared_data['oportunidade_id']}/favoritar", headers=headers)
    assert response.status_code == 204

def test_e2e_flow_esqueci_senha_nao_encontrado(e2e_client):
    response = e2e_client.post("/usuarios/esqueci-senha", json={"email": "naoexiste@teste.com"})
    assert response.status_code == 200

def test_e2e_flow_esqueci_senha_sucesso(e2e_client, shared_data):
    response = e2e_client.post("/usuarios/esqueci-senha", json={"email": shared_data["email"]})
    assert response.status_code == 200
