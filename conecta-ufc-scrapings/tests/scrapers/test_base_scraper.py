import pytest
import requests
from unittest.mock import patch, MagicMock
from app.scrapers.base_scraper import BaseScraper

@pytest.fixture
def base_scraper():
    return BaseScraper()

# --- Testes para fetch_html ---

@patch("app.scrapers.base_scraper.requests.get")
@patch("app.scrapers.base_scraper.sleep")
def test_fetch_html_sucesso_na_primeira_tentativa_retorna_html(mock_sleep, mock_get, base_scraper):
    # Arrange
    mock_response = MagicMock()
    mock_response.text = "<html>Sucesso</html>"
    mock_get.return_value = mock_response
    
    # Act
    resultado = base_scraper.fetch_html("http://teste.com")
    
    # Assert
    assert resultado == "<html>Sucesso</html>"
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_sleep.assert_not_called()

@patch("app.scrapers.base_scraper.requests.get")
@patch("app.scrapers.base_scraper.sleep")
def test_fetch_html_falha_inicial_mas_sucesso_depois_retorna_html(mock_sleep, mock_get, base_scraper):
    # Arrange
    mock_response_success = MagicMock()
    mock_response_success.text = "<html>Recuperado</html>"
    
    # Faz falhar na primeira, ter sucesso na segunda
    mock_get.side_effect = [
        requests.exceptions.ConnectionError("Falha conexao"),
        mock_response_success
    ]
    
    # Act
    resultado = base_scraper.fetch_html("http://teste.com")
    
    # Assert
    assert resultado == "<html>Recuperado</html>"
    assert mock_get.call_count == 2
    mock_sleep.assert_called_once_with(2)

@patch("app.scrapers.base_scraper.requests.get")
@patch("app.scrapers.base_scraper.sleep")
def test_fetch_html_falha_em_todas_tentativas_retorna_none(mock_sleep, mock_get, base_scraper):
    # Arrange
    mock_get.side_effect = requests.exceptions.Timeout("Timeout")
    
    # Act
    resultado = base_scraper.fetch_html("http://teste.com", retries=3)
    
    # Assert
    assert resultado is None
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 3

# --- Testes para normalizar_tipo ---

def test_normalizar_tipo_texto_com_paid_retorna_paid(base_scraper):
    # Arrange
    tipo_raw = "Edital"
    titulo = "Bolsa de PAID 2026"
    
    # Act
    resultado = base_scraper.normalizar_tipo(tipo_raw, titulo)
    
    # Assert
    assert resultado == "PAID"

def test_normalizar_tipo_texto_com_pibc_retorna_pibc(base_scraper):
    # Arrange
    tipo_raw = "Iniciação Científica"
    titulo = "Projeto UFC"
    
    # Act
    resultado = base_scraper.normalizar_tipo(tipo_raw, titulo)
    
    # Assert
    assert resultado == "PIBC"

def test_normalizar_tipo_texto_desconhecido_retorna_original(base_scraper):
    # Arrange
    tipo_raw = "Auxílio Moradia"
    titulo = "Edital 2026"
    
    # Act
    resultado = base_scraper.normalizar_tipo(tipo_raw, titulo)
    
    # Assert
    assert resultado == "Auxílio Moradia"
