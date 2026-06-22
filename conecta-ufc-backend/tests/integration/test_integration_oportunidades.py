import pytest
from app.models.oportunidade import OportunidadeDB, ResultadoDB, FavoritoDB
from app.core.auth import get_current_user_id
from app.main import app

# --- Helper para injetar um usuário mockado nas rotas que exigem autenticação ---
def mock_get_current_user_id():
    return "fake_keycloak_id_123"

@pytest.fixture
def override_auth():
    app.dependency_overrides[get_current_user_id] = mock_get_current_user_id
    yield
    app.dependency_overrides.clear()

# --- Testes de Integração para Oportunidades ---

def test_integration_oportunidades_listar_vazio_retorna_lista_vazia(client):
    response = client.get("/oportunidades")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total_elements"] == 0
    assert len(data["data"]) == 0

def test_integration_oportunidades_listar_com_dados_e_filtros(client, db_session):
    # Arrange
    op1 = OportunidadeDB(titulo="Bolsa Pesquisa", origem="UFC", tipo="PIBC", link="http://1", vagas=2, remuneracao=400)
    op2 = OportunidadeDB(titulo="Estágio", origem="UFC", tipo="Estágio", link="http://2", vagas=1, remuneracao=600)
    op3 = OportunidadeDB(titulo="Bolsa Extensão", origem="UFC", tipo="Extensão", link="http://3", vagas=1, remuneracao=400)
    db_session.add_all([op1, op2, op3])
    db_session.commit()

    # Act 1: Sem filtro
    resp1 = client.get("/oportunidades")
    assert resp1.status_code == 200
    assert resp1.json()["meta"]["total_elements"] == 3

    # Act 2: Filtrar por tipo PIBC
    resp2 = client.get("/oportunidades?tipo=PIBC")
    assert resp2.status_code == 200
    assert resp2.json()["meta"]["total_elements"] == 1
    assert resp2.json()["data"][0]["titulo"] == "Bolsa Pesquisa"

    # Act 3: Filtrar por texto na busca
    resp3 = client.get("/oportunidades?busca=Estágio")
    assert resp3.status_code == 200
    assert resp3.json()["meta"]["total_elements"] == 1
    assert resp3.json()["data"][0]["tipo"] == "Estágio"

def test_integration_oportunidades_paginacao_funciona_corretamente(client, db_session):
    # Arrange: Inserir 25 vagas
    vagas = [OportunidadeDB(titulo=f"Vaga {i}", origem="UFC", tipo="Bolsa", link=f"http://{i}") for i in range(25)]
    db_session.add_all(vagas)
    db_session.commit()

    # Act: Página 2, tamanho 10
    response = client.get("/oportunidades?page=2&size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 10
    assert data["meta"]["current_page"] == 2
    assert data["meta"]["total_pages"] == 3

def test_integration_oportunidades_favoritar_vaga_com_sucesso(client, db_session, override_auth):
    # Arrange
    vaga = OportunidadeDB(titulo="Vaga TOP", origem="UFC", tipo="Bolsa", link="http://top")
    db_session.add(vaga)
    db_session.commit()
    
    # Act
    response = client.post(f"/oportunidades/{vaga.id}/favoritar")
    
    # Assert
    assert response.status_code == 201
    assert "favoritada com sucesso" in response.json()["message"]
    
    favorito_no_banco = db_session.query(FavoritoDB).filter_by(usuario_id="fake_keycloak_id_123", oportunidade_id=vaga.id).first()
    assert favorito_no_banco is not None

def test_integration_oportunidades_favoritar_vaga_inexistente_retorna_404(client, override_auth):
    # Act
    response = client.post("/oportunidades/999/favoritar")
    # Assert
    assert response.status_code == 404

def test_integration_oportunidades_favoritar_vaga_ja_favoritada_retorna_201(client, db_session, override_auth):
    # Arrange
    vaga = OportunidadeDB(titulo="Vaga Repetida", origem="UFC", tipo="Bolsa", link="http://rep")
    db_session.add(vaga)
    db_session.commit()
    
    # Adiciona favorito manual
    fav = FavoritoDB(usuario_id="fake_keycloak_id_123", oportunidade_id=vaga.id)
    db_session.add(fav)
    db_session.commit()

    # Act
    response = client.post(f"/oportunidades/{vaga.id}/favoritar")
    
    # Assert
    assert response.status_code == 201
    assert "já está nos favoritos" in response.json()["message"].lower()

def test_integration_oportunidades_listar_favoritos_com_sucesso(client, db_session, override_auth):
    # Arrange: Inserir vagas
    op1 = OportunidadeDB(titulo="Favorito 1", origem="UFC", tipo="Bolsa", link="l1")
    op2 = OportunidadeDB(titulo="Favorito 2", origem="UFC", tipo="Bolsa", link="l2")
    op3 = OportunidadeDB(titulo="Nao Favorito", origem="UFC", tipo="Bolsa", link="l3")
    db_session.add_all([op1, op2, op3])
    db_session.commit()

    fav1 = FavoritoDB(usuario_id="fake_keycloak_id_123", oportunidade_id=op1.id)
    fav2 = FavoritoDB(usuario_id="fake_keycloak_id_123", oportunidade_id=op2.id)
    db_session.add_all([fav1, fav2])
    db_session.commit()
    
    # Act
    response = client.get("/oportunidades/favoritos")
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert len(dados) == 2
    titulos = [item["titulo"] for item in dados]
    assert "Favorito 1" in titulos
    assert "Favorito 2" in titulos
    assert "Nao Favorito" not in titulos

def test_integration_oportunidades_remover_favorito(client, db_session, override_auth):
    # Arrange
    vaga = OportunidadeDB(titulo="Remover Fav", origem="UFC", tipo="Bolsa", link="http://rem")
    db_session.add(vaga)
    db_session.commit()
    
    fav = FavoritoDB(usuario_id="fake_keycloak_id_123", oportunidade_id=vaga.id)
    db_session.add(fav)
    db_session.commit()

    # Act
    response = client.delete(f"/oportunidades/{vaga.id}/favoritar")
    
    # Assert
    assert response.status_code == 204
    favorito_no_banco = db_session.query(FavoritoDB).filter_by(usuario_id="fake_keycloak_id_123", oportunidade_id=vaga.id).first()
    assert favorito_no_banco is None
