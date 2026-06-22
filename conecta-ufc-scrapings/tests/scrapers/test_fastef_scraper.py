import pytest
from unittest.mock import patch, MagicMock
from app.scrapers.fastef_scraper import FastefScraper

@pytest.fixture
def scraper():
    return FastefScraper()

# --- Testes para run ---

@patch.object(FastefScraper, "fetch_html")
@patch.object(FastefScraper, "parse_html")
def test_run_html_sucesso_chama_parse_html(mock_parse, mock_fetch, scraper):
    # Arrange
    mock_fetch.return_value = "<html>OK</html>"
    mock_parse.return_value = [{"vaga": 1}]
    
    # Act
    resultado = scraper.run()
    
    # Assert
    assert resultado == [{"vaga": 1}]
    mock_fetch.assert_called_once_with("https://fastef.ufc.br/processos-seletivos/")
    mock_parse.assert_called_once_with("<html>OK</html>")

@patch.object(FastefScraper, "fetch_html")
def test_run_html_falha_retorna_lista_vazia(mock_fetch, scraper):
    # Arrange
    mock_fetch.return_value = None
    
    # Act
    resultado = scraper.run()
    
    # Assert
    assert resultado == []

# --- Testes para parse_html ---

@patch("app.scrapers.fastef_scraper.PdfParser.extrair_dados")
def test_parse_html_com_cartoes_validos_retorna_lista_mapeada(mock_pdf_parser, scraper):
    # Arrange
    html = """
    <html>
        <body>
            <div class="vc_grid-item">
                <h4>Edital de Seleção FASTEF</h4>
                <a class="vc_btn3" href="http://link.com/edital">Clique aqui</a>
            </div>
        </body>
    </html>
    """
    mock_pdf_parser.return_value = {
        "data_inicio": "2026-01-01",
        "data_fim": "2026-02-01",
        "remuneracao": 500.0,
        "vagas": 2,
        "coordenador": "Prof. FASTEF",
        "descricao": "Descricao do edital"
    }
    
    # Act
    resultado = scraper.parse_html(html)
    
    # Assert
    assert len(resultado) == 1
    vaga = resultado[0]
    assert vaga["titulo"] == "Edital de Seleção FASTEF"
    assert vaga["link"] == "http://link.com/edital"
    assert vaga["remuneracao"] == 500.0
    mock_pdf_parser.assert_called_once_with("http://link.com/edital", "Edital de Seleção FASTEF")

@patch("app.scrapers.fastef_scraper.PdfParser.extrair_dados")
def test_parse_html_sem_cartoes_retorna_lista_vazia(mock_pdf_parser, scraper):
    # Arrange
    html = "<html><body><div>Vazio</div></body></html>"
    
    # Act
    resultado = scraper.parse_html(html)
    
    # Assert
    assert resultado == []
    mock_pdf_parser.assert_not_called()

@patch("app.scrapers.fastef_scraper.PdfParser.extrair_dados")
def test_parse_html_cartao_sem_titulo_nao_adiciona_oportunidade(mock_pdf_parser, scraper):
    # Arrange
    html = """
    <html>
        <body>
            <div class="vc_grid-item">
                <a class="vc_btn3" href="http://link.com/edital">Sem título</a>
            </div>
        </body>
    </html>
    """
    
    # Act
    resultado = scraper.parse_html(html)
    
    # Assert
    assert resultado == []
    mock_pdf_parser.assert_not_called()
