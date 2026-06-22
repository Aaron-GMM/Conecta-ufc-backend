import pytest
from unittest.mock import patch, MagicMock
from app.api.routers.scraper_routes import rodar_sincronizacao, rodar_scraper_ufc, rodar_scraper_fastef
from app.models.oportunidade import OportunidadeDB, ResultadoDB

@patch("app.api.routers.scraper_routes.SyncService")
def test_rodar_sincronizacao_retorna_sucesso(mock_sync):
    # Arrange
    mock_instance = MagicMock()
    mock_sync.return_value = mock_instance
    
    # Act
    response = rodar_sincronizacao()
    
    # Assert
    assert response["status"] == "Sincronização iniciada manualmente"
    mock_instance.sync.assert_called_once()

@patch("app.api.routers.scraper_routes.UfcScraper")
def test_rodar_scraper_ufc_com_vagas_novas_salva_no_banco(mock_ufc_scraper):
    # Arrange
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_ufc_scraper.return_value = mock_scraper_instance
    
    vaga_mock = {
        "titulo": "Nova", "origem": "UFC", "tipo": "Bolsa", "link": "http://1",
        "data_inicio": None, "data_fim": None, "remuneracao": None, "vagas": None,
        "coordenador": None, "descricao": None,
        "resultados": [{"titulo": "Res 1", "link": "http://res1"}]
    }
    mock_scraper_instance.run.return_value = [vaga_mock]
    
    # Simula que as vagas e resultados não existem no banco
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = None
    
    # Act
    res = rodar_scraper_ufc(mock_db)
    
    # Assert
    assert res["status"] == "sucesso"
    assert res["editais_salvos"] == 1
    assert res["resultados_salvos"] == 1
    assert mock_db.add.call_count == 2 # 1 Vaga, 1 Resultado
    mock_db.commit.assert_called_once()

@patch("app.api.routers.scraper_routes.UfcScraper")
def test_rodar_scraper_ufc_com_vagas_duplicadas_ignora(mock_ufc_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_ufc_scraper.return_value = mock_scraper_instance
    
    vaga_mock = {
        "titulo": "Velha", "origem": "UFC", "tipo": "Bolsa", "link": "http://1"
    }
    # Duas vagas com o mesmo link
    mock_scraper_instance.run.return_value = [vaga_mock, vaga_mock]
    
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock() # Já existe
    
    res = rodar_scraper_ufc(mock_db)
    
    assert res["editais_salvos"] == 0
    assert res["editais_ignorados_por_duplicidade"] == 2

@patch("app.api.routers.scraper_routes.FastefScraper")
def test_rodar_scraper_fastef_com_vagas_novas_e_resultados(mock_fastef_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_fastef_scraper.return_value = mock_scraper_instance
    
    edital = {"titulo": "Edital 01/2026", "origem": "FASTEF", "tipo": "Bolsa", "link": "http://e1"}
    resultado = {"titulo": "Resultado Edital 01/2026", "origem": "FASTEF", "tipo": "Bolsa", "link": "http://r1"}
    
    mock_scraper_instance.run.return_value = [edital, resultado]
    mock_db.query.return_value.filter.return_value.first.return_value = None # Nada existe
    
    res = rodar_scraper_fastef(mock_db)
    
    assert res["status"] == "sucesso"
    # Salva o edital real
    # Tenta salvar o resultado: procura o pai pelo regex, não acha, cria o fantasma (se for o caso), e salva o resultado
    # Total de salvos deve ser pelo menos 1 edital + 1 resultado
    mock_db.commit.assert_called_once()

@patch("app.api.routers.scraper_routes.FastefScraper")
def test_rodar_scraper_fastef_com_fantasma_sendo_atualizado(mock_fastef_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_fastef_scraper.return_value = mock_scraper_instance
    
    edital = {"titulo": "Edital 02/2026", "origem": "FASTEF", "tipo": "Bolsa", "link": "http://e2", "data_inicio": None, "data_fim": None, "remuneracao": None, "vagas": None, "coordenador": None, "descricao": None}
    mock_scraper_instance.run.return_value = [edital]
    
    # 1st query: check if exists by link -> False
    # 2nd query: check if fantasma exists -> True
    fantasma_mock = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, fantasma_mock]
    
    res = rodar_scraper_fastef(mock_db)
    
    # Fantasma deveria ser atualizado
    assert fantasma_mock.titulo == "Edital 02/2026"
    assert res["editais_salvos"] == 0

@patch("app.api.routers.scraper_routes.FastefScraper")
def test_rodar_scraper_fastef_resultados_soltos(mock_fastef_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_fastef_scraper.return_value = mock_scraper_instance
    
    resultado_solto = {"titulo": "Resultado Final Aleatorio", "origem": "FASTEF", "tipo": "Bolsa", "link": "http://res"}
    mock_scraper_instance.run.return_value = [resultado_solto]
    
    # Simula que a vaga solta não existe
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    res = rodar_scraper_fastef(mock_db)
    assert res["editais_salvos"] == 1  # Salvou como vaga normal porque não achou padrão edital

@patch("app.api.routers.scraper_routes.UfcScraper")
def test_rodar_scraper_ufc_com_resultados_duplicados_na_mesma_execucao(mock_ufc_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_ufc_scraper.return_value = mock_scraper_instance
    
    vaga_mock = {
        "titulo": "Nova", "origem": "UFC", "tipo": "Bolsa", "link": "http://1",
        "resultados": [
            {"titulo": "Res 1", "link": "http://res1"},
            {"titulo": "Res 1 Duplicado", "link": "http://res1"}
        ]
    }
    mock_scraper_instance.run.return_value = [vaga_mock]
    
    mock_db.query.return_value.filter.return_value.first.return_value = None
    res = rodar_scraper_ufc(mock_db)
    
    assert res["resultados_salvos"] == 1

@patch("app.api.routers.scraper_routes.FastefScraper")
def test_rodar_scraper_fastef_edital_ja_existe(mock_fastef_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_fastef_scraper.return_value = mock_scraper_instance
    
    edital = {"titulo": "Edital 01/2026", "origem": "FASTEF", "tipo": "Bolsa", "link": "http://e1"}
    mock_scraper_instance.run.return_value = [edital]
    
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock() # Já existe
    
    res = rodar_scraper_fastef(mock_db)
    assert res["editais_salvos"] == 0
    assert res["ignorados_por_duplicidade"] == 1

@patch("app.api.routers.scraper_routes.FastefScraper")
def test_rodar_scraper_fastef_resultados_soltos_ja_existem(mock_fastef_scraper):
    mock_db = MagicMock()
    mock_scraper_instance = MagicMock()
    mock_fastef_scraper.return_value = mock_scraper_instance
    
    resultado_solto = {"titulo": "Resultado Final Aleatorio", "origem": "FASTEF", "tipo": "Bolsa", "link": "http://res"}
    mock_scraper_instance.run.return_value = [resultado_solto]
    
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock() # Já existe
    
    res = rodar_scraper_fastef(mock_db)
    assert res["editais_salvos"] == 0
    assert res["ignorados_por_duplicidade"] == 1
