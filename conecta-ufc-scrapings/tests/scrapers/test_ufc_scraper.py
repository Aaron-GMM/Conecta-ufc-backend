import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.scrapers.ufc_scraper import UfcScraper

@pytest.fixture
def scraper():
    return UfcScraper()

# --- Testes para _extrair_datas ---

def test_extrair_datas_padrao_simples_retorna_datas(scraper):
    # Arrange
    texto = "Inscrições abertas de 15 a 20 de março de 2026."
    
    # Act
    data_inicio, data_fim = scraper._extrair_datas(texto)
    
    # Assert
    assert data_inicio == datetime(2026, 3, 15)
    assert data_fim == datetime(2026, 3, 20)

def test_extrair_datas_padrao_curto_retorna_datas(scraper):
    # Arrange
    texto = "Período: 01/04 a 10/04/2026."
    
    # Act
    data_inicio, data_fim = scraper._extrair_datas(texto)
    
    # Assert
    assert data_inicio == datetime(2026, 4, 1)
    assert data_fim == datetime(2026, 4, 10)

def test_extrair_datas_texto_vazio_retorna_none(scraper):
    assert scraper._extrair_datas("") == (None, None)
    assert scraper._extrair_datas(None) == (None, None)

def test_extrair_datas_texto_sem_data_retorna_none(scraper):
    assert scraper._extrair_datas("O edital não tem datas.") == (None, None)

# --- Testes para run ---

@patch.object(UfcScraper, "fetch_html")
@patch.object(UfcScraper, "parse_html")
def test_run_sucesso_chama_parse(mock_parse, mock_fetch, scraper):
    # Arrange
    mock_fetch.return_value = "<html>OK</html>"
    mock_parse.return_value = [{"vaga": "UFC"}]
    
    # Act
    resultado = scraper.run()
    
    # Assert
    assert resultado == [{"vaga": "UFC"}]
    mock_fetch.assert_called_once()
    mock_parse.assert_called_once()

@patch.object(UfcScraper, "fetch_html")
def test_run_falha_html_retorna_vazio(mock_fetch, scraper):
    mock_fetch.return_value = None
    assert scraper.run() == []

# --- Testes para parse_html ---

@patch("app.scrapers.ufc_scraper.PdfParser.extrair_dados")
def test_parse_html_valido_retorna_lista_mapeada(mock_pdf_parser, scraper):
    # Arrange
    html = """
    <html>
        <body>
            <article class="hrf-entry">
                <h3 class="hrf-title">Bolsa de Extensão</h3>
                <div class="hrf-content">
                    <h4>Projeto de Teste UFC</h4>
                    <ul>
                        <li>Inscrições de 10 a 20 de maio de 2026</li>
                        <li><a href="http://link.com/edital_teste.pdf">Edital de Seleção</a></li>
                        <li><a href="http://link.com/anexo">Anexo</a></li>
                    </ul>
                </div>
            </article>
        </body>
    </html>
    """
    mock_pdf_parser.return_value = {
        "remuneracao": 400.0,
        "vagas": 1,
        "coordenador": "Prof. UFC",
        "descricao": "Descricao",
        "data_inicio": None,
        "data_fim": None
    }
    
    # Act
    resultado = scraper.parse_html(html)
    
    # Assert
    assert len(resultado) == 1
    vaga = resultado[0]
    assert vaga["titulo"] == "Projeto de Teste UFC"
    assert vaga["origem"] == "UFC-Quixadá"
    assert vaga["tipo"] == "Extensão"
    assert vaga["link"] == "http://link.com/edital_teste.pdf"
    assert vaga["data_inicio"] == datetime(2026, 5, 10) # Pego pelo HTML
    assert vaga["remuneracao"] == 400.0
    assert len(vaga["resultados"]) == 1
    assert vaga["resultados"][0]["titulo"] == "Anexo"

@patch("app.scrapers.ufc_scraper.PdfParser.extrair_dados")
def test_parse_html_sem_link_de_edital_ignora(mock_pdf_parser, scraper):
    # Arrange
    html = """
    <html>
        <body>
            <article class="hrf-entry">
                <h3 class="hrf-title">Bolsa</h3>
                <div class="hrf-content">
                    <ul>
                        <li><a href="http://link.com/anexo">Outro link</a></li>
                    </ul>
                </div>
            </article>
        </body>
    </html>
    """
    
    # Act
    resultado = scraper.parse_html(html)
    
    # Assert
    assert resultado == []
    mock_pdf_parser.assert_not_called()
