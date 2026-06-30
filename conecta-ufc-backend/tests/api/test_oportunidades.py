import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.oportunidade import OportunidadeDB, FavoritoDB
from app.core.auth import get_current_user_id
from app.db.database import get_db
from app.api.routes.oportunidades import paginar_resultados

client = TestClient(app)

# Fixtures de Mocks
@pytest.fixture
def mock_db_session(mocker):
    return mocker.MagicMock()

@pytest.fixture
def override_dependencies(mock_db_session):
    # Override das dependências do FastAPI
    app.dependency_overrides[get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user_id] = lambda: "user_test_123"
    yield
    app.dependency_overrides = {}

# --- Testes para listar_oportunidades ---

def test_listar_oportunidades_sem_filtros_retorna_paginacao_correta(mock_db_session, override_dependencies):
    # Arrange
    mock_query = mock_db_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_options.count.return_value = 25
    mock_order = mock_options.order_by.return_value
    mock_offset = mock_order.offset.return_value
    mock_limit = mock_offset.limit.return_value
    
    # Mockando duas oportunidades falsas com campos obrigatórios
    op1 = OportunidadeDB(id=1, titulo="Op 1", origem="UFC", tipo="Bolsa", link="url", data_inicio="2026-01-01", data_fim="2026-12-31", vagas=1, remuneracao=500.0, resultados=[])
    op2 = OportunidadeDB(id=2, titulo="Op 2", origem="UFC", tipo="Estágio", link="url", data_inicio="2026-01-01", data_fim="2026-12-31", vagas=1, remuneracao=500.0, resultados=[])
    mock_limit.all.return_value = [op1, op2]
    
    # Act
    response = client.get("/oportunidades?page=1&size=20")
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["meta"]["total_elements"] == 25
    assert dados["meta"]["total_pages"] == 2
    assert dados["meta"]["has_next"] is True
    assert len(dados["data"]) == 2

def test_listar_oportunidades_com_filtros_aplica_filtros_na_query(mock_db_session, override_dependencies):
    # Arrange
    mock_query = mock_db_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_filter1 = mock_options.filter.return_value
    mock_filter2 = mock_filter1.filter.return_value
    mock_filter3 = mock_filter2.filter.return_value
    
    mock_filter3.count.return_value = 5
    
    mock_order = mock_filter3.order_by.return_value
    mock_offset = mock_order.offset.return_value
    mock_limit = mock_offset.limit.return_value
    mock_limit.all.return_value = []
    
    # Act
    response = client.get("/oportunidades?busca=bolsa&origem=UFC&tipo=Extensao")
    
    # Assert
    assert response.status_code == 200
    # Verifica se os três filtros foram encadeados (mock_filter.filter chamado)
    assert mock_options.filter.call_count == 1
    assert mock_filter1.filter.call_count == 1
    assert mock_filter2.filter.call_count == 1


def test_listar_oportunidades_ordenadas_a_z_retorna_lista_ordenada(mock_db_session, override_dependencies):
    mock_query = mock_db_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_options.count.return_value = 1
    mock_order = mock_options.order_by.return_value
    mock_offset = mock_order.offset.return_value
    mock_limit = mock_offset.limit.return_value
    mock_limit.all.return_value = [
        OportunidadeDB(
            id=1,
            titulo="Bolsa A",
            origem="UFC",
            tipo="Bolsa",
            link="url-a",
            data_inicio="2026-01-01",
            data_fim="2026-12-31",
            vagas=1,
            remuneracao=500.0,
            resultados=[],
        )
    ]

    response = client.get("/oportunidades/ordenadas/a-z?page=1&size=20")

    assert response.status_code == 200
    dados = response.json()
    assert dados["meta"]["total_elements"] == 1
    assert dados["data"][0]["titulo"] == "Bolsa A"
    criterios = mock_options.order_by.call_args.args
    assert "lower(oportunidades.titulo) ASC NULLS LAST" in str(criterios[0])
    assert "oportunidades.id ASC" in str(criterios[1])


def test_listar_oportunidades_ordenadas_por_recencia_retorna_lista_ordenada(mock_db_session, override_dependencies):
    mock_query = mock_db_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_options.count.return_value = 1
    mock_order = mock_options.order_by.return_value
    mock_offset = mock_order.offset.return_value
    mock_limit = mock_offset.limit.return_value
    mock_limit.all.return_value = [
        OportunidadeDB(
            id=2,
            titulo="Bolsa Nova",
            origem="UFC",
            tipo="Estágio",
            link="url-b",
            data_inicio="2026-01-01",
            data_fim="2026-12-31",
            vagas=2,
            remuneracao=800.0,
            resultados=[],
        )
    ]

    response = client.get("/oportunidades/ordenadas/mais-recentes?page=1&size=20")

    assert response.status_code == 200
    dados = response.json()
    assert dados["meta"]["total_elements"] == 1
    assert dados["data"][0]["titulo"] == "Bolsa Nova"
    criterios = mock_options.order_by.call_args.args
    assert "oportunidades.data_inicio DESC NULLS LAST" in str(criterios[0])
    assert "oportunidades.data_criacao DESC NULLS LAST" in str(criterios[1])
    assert "oportunidades.id DESC" in str(criterios[2])


def test_paginar_resultados_sem_criterio_aplica_ordem_padrao_estavel():
    query = MagicMock()
    query.count.return_value = 0
    query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

    resultado = paginar_resultados(query, page=1, size=20)

    criterios = query.order_by.call_args.args
    assert "oportunidades.data_criacao DESC NULLS LAST" in str(criterios[0])
    assert "oportunidades.id DESC" in str(criterios[1])
    assert resultado["data"] == []

# --- Testes para favoritar_oportunidade ---

def test_favoritar_oportunidade_vaga_nao_existe_retorna_404(mock_db_session, override_dependencies):
    # Arrange
    # Ajustando o mock para que a chamada encadeada retorne None
    mock_db_session.query.return_value.filter.return_value.first.return_value = None  # Vaga não encontrada
    
    # Act
    response = client.post("/oportunidades/999/favoritar")
    
    # Assert
    assert response.status_code == 404
    assert "Oportunidade não encontrada" in response.json()["mensagem"]

def test_favoritar_oportunidade_ja_favoritada_retorna_mensagem_201(mock_db_session, override_dependencies):
    # Arrange
    # Primeiro filtro (OportunidadeDB) retorna vaga
    # Segundo filtro (FavoritoDB) retorna favorito existente
    op_mock = MagicMock()
    fav_mock = MagicMock()
    
    def side_effect_first():
        # A query é chamada duas vezes na rota, para Oportunidade e depois para Favorito
        # Mas encadeia com filters. O MagicMock mantém o rastreamento, usaremos side_effect no .first()
        yield op_mock
        yield fav_mock

    mock_db_session.query.return_value.filter.return_value.first.side_effect = side_effect_first()
    
    # Act
    response = client.post("/oportunidades/1/favoritar")
    
    # Assert
    assert response.status_code == 201
    assert response.json()["message"] == "Oportunidade já está nos favoritos"

def test_favoritar_oportunidade_sucesso_adiciona_favorito(mock_db_session, override_dependencies):
    # Arrange
    op_mock = MagicMock()
    def side_effect_first():
        yield op_mock # Vaga existe
        yield None    # Favorito não existe

    mock_db_session.query.return_value.filter.return_value.first.side_effect = side_effect_first()
    
    # Act
    response = client.post("/oportunidades/1/favoritar")
    
    # Assert
    assert response.status_code == 201
    assert response.json()["message"] == "Oportunidade favoritada com sucesso"
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()

# --- Testes para remover_favorito ---

def test_remover_favorito_nao_encontrado_retorna_404(mock_db_session, override_dependencies):
    # Arrange
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    # Act
    response = client.delete("/oportunidades/1/favoritar")
    
    # Assert
    assert response.status_code == 404

def test_remover_favorito_sucesso_remove_favorito(mock_db_session, override_dependencies):
    # Arrange
    fav_mock = MagicMock()
    mock_db_session.query.return_value.filter.return_value.first.return_value = fav_mock
    
    # Act
    response = client.delete("/oportunidades/1/favoritar")
    
    # Assert
    assert response.status_code == 204
    mock_db_session.delete.assert_called_once_with(fav_mock)
    mock_db_session.commit.assert_called_once()

# --- Testes para listar_favoritos ---

def test_listar_favoritos_retorna_lista_de_vagas(mock_db_session, override_dependencies):
    query = (
        mock_db_session.query.return_value
        .join.return_value
        .filter.return_value
        .options.return_value
    )
    query.count.return_value = 2
    resultados = query.order_by.return_value.offset.return_value.limit.return_value
    resultados.all.return_value = [
        OportunidadeDB(
            id=10,
            titulo="Bolsa A",
            origem="UFC",
            tipo="Bolsa",
            link="l1",
            resultados=[],
        ),
        OportunidadeDB(
            id=20,
            titulo="Bolsa B",
            origem="UFC",
            tipo="Bolsa",
            link="l2",
            resultados=[],
        ),
    ]
    
    # Act
    response = client.get("/oportunidades/favoritos")
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["meta"]["total_elements"] == 2
    assert len(dados["data"]) == 2
    assert dados["data"][0]["titulo"] == "Bolsa A"
