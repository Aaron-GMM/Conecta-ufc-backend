import pytest
import io
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.scrapers.pdf_parser import PdfParser

@pytest.fixture
def parser():
    return PdfParser()

# --- Testes para _converter_str_para_float ---

def test_converter_str_para_float_valor_valido_retorna_float(parser):
    assert parser._converter_str_para_float("400,00") == 400.0
    assert parser._converter_str_para_float("1.200,50") == 1200.5
    assert parser._converter_str_para_float("400") == 400.0

def test_converter_str_para_float_valor_invalido_retorna_zero(parser):
    assert parser._converter_str_para_float("valor") == 0.0

# --- Testes para _obter_bytes_do_pdf ---

def test_obter_bytes_do_pdf_onedrive_ignorado(parser):
    assert parser._obter_bytes_do_pdf("http://1drv.ms/arquivo") is None

@patch("app.scrapers.pdf_parser.requests.get")
def test_obter_bytes_do_pdf_link_direto_pdf_retorna_bytes(mock_get, parser):
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.content = b"%PDF-1.4"
    mock_get.return_value = mock_resp
    
    result = parser._obter_bytes_do_pdf("http://site.com/edital.pdf")
    assert isinstance(result, io.BytesIO)
    assert result.read() == b"%PDF-1.4"

@patch("app.scrapers.pdf_parser.requests.get")
def test_obter_bytes_do_pdf_html_com_link_pdf_retorna_bytes(mock_get, parser):
    mock_resp_html = MagicMock()
    mock_resp_html.headers = {"Content-Type": "text/html"}
    mock_resp_html.text = '<html><body><a href="arquivo.pdf">Download</a></body></html>'
    
    mock_resp_pdf = MagicMock()
    mock_resp_pdf.headers = {"Content-Type": "application/pdf"}
    mock_resp_pdf.content = b"PDF-DATA"
    
    # Primeiro call: HTML. Segundo call: PDF
    mock_get.side_effect = [mock_resp_html, mock_resp_pdf]
    
    result = parser._obter_bytes_do_pdf("http://site.com/pagina")
    assert isinstance(result, io.BytesIO)
    assert result.read() == b"PDF-DATA"

@patch("app.scrapers.pdf_parser.requests.get")
def test_obter_bytes_do_pdf_erro_requisicao_retorna_none(mock_get, parser):
    mock_get.side_effect = Exception("Erro rede")
    assert parser._obter_bytes_do_pdf("http://site.com/pdf") is None

# --- Testes para extrair_dados ---

def test_extrair_dados_titulo_com_resultado_retorna_dicionario_vazio(parser):
    res = parser.extrair_dados("http://site.com", "Resultado Final")
    assert res["remuneracao"] is None
    assert res["vagas"] is None

@patch("app.scrapers.pdf_parser.pdfplumber.open")
@patch.object(PdfParser, "_obter_bytes_do_pdf")
def test_extrair_dados_pdf_completo_retorna_dados(mock_obter, mock_pdf_open, parser):
    # Arrange
    mock_obter.return_value = io.BytesIO(b"fake")
    
    # Mock do texto do PDF simulando um edital
    texto = "O valor da bolsa é de R$ 400,00.\n" \
            "Serão ofertadas 2 vagas para o projeto.\n" \
            "Inscrições no período de 15/03/2026 a 20/03/2026.\n" \
            "Coordenador: Carlos Silva.\n" \
            "1. OBJETO\nEste edital visa selecionar alunos para o projeto."
            
    mock_page = MagicMock()
    mock_page.extract_text.return_value = texto
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__.return_value = mock_pdf
    mock_pdf_open.return_value = mock_pdf
    
    # Act
    res = parser.extrair_dados("http://site.com", "Edital de Seleção")
    
    # Assert
    assert res["remuneracao"] == 400.0
    assert res["vagas"] == 2
    assert res["data_inicio"] == datetime(2026, 3, 15)
    assert res["data_fim"] == datetime(2026, 3, 20)
    assert "Carlos Silva" in res["coordenador"]
    assert "Este edital visa selecionar alunos" in res["descricao"]

@patch("app.scrapers.pdf_parser.pdfplumber.open")
@patch.object(PdfParser, "_obter_bytes_do_pdf")
def test_extrair_dados_data_extenso(mock_obter, mock_pdf_open, parser):
    mock_obter.return_value = io.BytesIO(b"fake")
    texto = "25 de fevereiro de 2026 a 04 de março de 2026. Prof. Maria"
    mock_page = MagicMock()
    mock_page.extract_text.return_value = texto
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__.return_value = mock_pdf
    mock_pdf_open.return_value = mock_pdf
    
    res = parser.extrair_dados("http://site.com", "Edital Data Extenso")
    assert res["data_inicio"] == datetime(2026, 2, 25)
    assert res["data_fim"] == datetime(2026, 3, 4)

@patch("app.scrapers.pdf_parser.pdfplumber.open")
@patch.object(PdfParser, "_obter_bytes_do_pdf")
def test_extrair_dados_fallback_descricao(mock_obter, mock_pdf_open, parser):
    mock_obter.return_value = io.BytesIO(b"fake")
    # Um texto longo sem palavra "objeto"
    texto = "Aqui está um texto longo. " * 20
    mock_page = MagicMock()
    mock_page.extract_text.return_value = texto
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__.return_value = mock_pdf
    mock_pdf_open.return_value = mock_pdf
    
    res = parser.extrair_dados("http://site.com", "Edital sem objeto")
    assert res["descricao"] is not None
    assert len(res["descricao"]) > 0

@patch.object(PdfParser, "_obter_bytes_do_pdf")
def test_extrair_dados_falha_ao_obter_pdf_retorna_vazio(mock_obter, parser):
    mock_obter.return_value = None
    res = parser.extrair_dados("http://site.com", "Edital quebrando")
    assert res["remuneracao"] is None

@patch.object(PdfParser, "_obter_bytes_do_pdf")
def test_extrair_dados_falha_no_pdfplumber_retorna_vazio(mock_obter, parser):
    mock_obter.return_value = io.BytesIO(b"badpdf")
    
    with patch("app.scrapers.pdf_parser.pdfplumber.open", side_effect=Exception("Corrupted PDF")):
        res = parser.extrair_dados("http://site.com", "Edital corrompido")
        assert res["remuneracao"] is None
        assert res["vagas"] is None

@patch("app.scrapers.pdf_parser.requests.get")
def test_obter_bytes_do_pdf_google_drive(mock_get, parser):
    mock_resp_html = MagicMock()
    mock_resp_html.headers = {"Content-Type": "text/html"}
    mock_resp_html.text = '<html><body><a href="https://drive.google.com/file/d/1234abc">Drive</a></body></html>'
    
    mock_resp_drive = MagicMock()
    mock_resp_drive.content = b"DRIVE-PDF"
    
    mock_get.side_effect = [mock_resp_html, mock_resp_drive]
    
    result = parser._obter_bytes_do_pdf("http://site.com/drive")
    assert isinstance(result, io.BytesIO)
    assert result.read() == b"DRIVE-PDF"

@patch.object(PdfParser, "_obter_bytes_do_pdf")
def test_extrair_dados_data_curta_apenas_dia_mes(mock_obter, parser):
    mock_obter.return_value = io.BytesIO(b"fake")
    texto = "Inscrições 25/02 a 03/03/2026. Prof. Joao"
    mock_page = MagicMock()
    mock_page.extract_text.return_value = texto
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__.return_value = mock_pdf
    
    with patch("app.scrapers.pdf_parser.pdfplumber.open", return_value=mock_pdf):
        res = parser.extrair_dados("http://site.com", "Edital")
        assert res["data_inicio"] == datetime(2026, 2, 25)
        assert res["data_fim"] == datetime(2026, 3, 3)
