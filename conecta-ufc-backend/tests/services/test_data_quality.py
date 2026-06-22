import pytest
from unittest.mock import patch, MagicMock
import requests
from app.services.data_quality import link_acessivel, is_dado_valido, filtrar_oportunidades_qualificadas
from app.schemas.oportunidade import OportunidadeSync

# --- Testes para link_acessivel ---

def test_link_acessivel_url_vazia_retorna_false():
    # Arrange
    url = ""
    
    # Act
    resultado = link_acessivel(url)
    
    # Assert
    assert resultado is False

@patch("app.services.data_quality.requests.head")
def test_link_acessivel_head_retorna_200_retorna_true(mock_head):
    # Arrange
    url = "http://site-valido.com"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_head.return_value = mock_response
    
    # Act
    resultado = link_acessivel(url)
    
    # Assert
    assert resultado is True
    mock_head.assert_called_once()

@patch("app.services.data_quality.requests.head")
def test_link_acessivel_head_retorna_404_retorna_false(mock_head):
    # Arrange
    url = "http://site-invalido.com"
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_head.return_value = mock_response
    
    # Act
    resultado = link_acessivel(url)
    
    # Assert
    assert resultado is False

@patch("app.services.data_quality.requests.get")
@patch("app.services.data_quality.requests.head")
def test_link_acessivel_head_falha_mas_get_retorna_200_retorna_true(mock_head, mock_get):
    # Arrange
    url = "http://site-bloqueia-head.com"
    mock_head.side_effect = requests.RequestException("HEAD blocked")
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_get.return_value = mock_response_get
    
    # Act
    resultado = link_acessivel(url)
    
    # Assert
    assert resultado is True
    mock_head.assert_called_once()
    mock_get.assert_called_once()

@patch("app.services.data_quality.requests.get")
@patch("app.services.data_quality.requests.head")
def test_link_acessivel_head_e_get_falham_retorna_false(mock_head, mock_get):
    # Arrange
    url = "http://site-morto.com"
    mock_head.side_effect = requests.RequestException("HEAD blocked")
    mock_get.side_effect = requests.RequestException("GET failed too")
    
    # Act
    resultado = link_acessivel(url)
    
    # Assert
    assert resultado is False
    mock_head.assert_called_once()
    mock_get.assert_called_once()

# --- Testes para is_dado_valido ---

def test_is_dado_valido_titulo_vazio_retorna_false():
    # Arrange
    item = OportunidadeSync(titulo="", origem="UFC", tipo="Bolsa", link="http://link.com")
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is False

def test_is_dado_valido_titulo_sem_titulo_retorna_false():
    # Arrange
    item = OportunidadeSync(titulo="Sem Título", origem="UFC", tipo="Bolsa", link="http://link.com")
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is False

def test_is_dado_valido_link_vazio_retorna_false():
    # Arrange
    item = OportunidadeSync(titulo="Vaga Legal", origem="UFC", tipo="Bolsa", link="")
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is False

def test_is_dado_valido_dados_preenchidos_retorna_true():
    # Arrange
    item = OportunidadeSync(
        titulo="Vaga de Extensão",
        origem="UFC",
        tipo="Extensão",
        link="http://link-valido.com",
        data_inicio="2026-01-01",
        data_fim="2026-12-31",
        remuneracao=700.0,
        vagas=2
    )
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is True

@patch("app.services.data_quality.link_acessivel")
def test_is_dado_valido_quatro_campos_vazios_e_link_inacessivel_retorna_false(mock_link_acessivel):
    # Arrange
    item = OportunidadeSync(
        titulo="Vaga Fantasma",
        origem="UFC",
        tipo="Bolsa",
        link="http://link-quebrado.com",
        data_inicio=None,
        data_fim=None,
        remuneracao=None,
        vagas=None
    )
    mock_link_acessivel.return_value = False
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is False
    mock_link_acessivel.assert_called_once_with(item.link)

@patch("app.services.data_quality.link_acessivel")
def test_is_dado_valido_quatro_campos_vazios_mas_link_acessivel_retorna_false(mock_link_acessivel):
    # Arrange
    item = OportunidadeSync(
        titulo="Vaga Vazia mas Link Funciona",
        origem="UFC",
        tipo="Bolsa",
        link="http://link-funciona.com",
        data_inicio=None,
        data_fim=None,
        remuneracao=None,
        vagas=None
    )
    mock_link_acessivel.return_value = True
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is False  # O código atual rejeita vagas que estejam 100% vazias
    mock_link_acessivel.assert_called_once_with(item.link)

def test_is_dado_valido_um_campo_preenchido_retorna_true():
    # Arrange
    item = OportunidadeSync(
        titulo="Vaga com Data",
        origem="UFC",
        tipo="Bolsa",
        link="http://link-funciona.com",
        data_inicio="2026-06-20",
        data_fim=None,
        remuneracao=None,
        vagas=None
    )
    
    # Act
    resultado = is_dado_valido(item)
    
    # Assert
    assert resultado is True

# --- Testes para filtrar_oportunidades_qualificadas ---

@patch("app.services.data_quality.is_dado_valido")
def test_filtrar_oportunidades_qualificadas_separa_validos_e_invalidos_retorna_apenas_validos(mock_is_dado_valido):
    # Arrange
    item_valido = OportunidadeSync(titulo="Válida", origem="A", tipo="B", link="http://ok.com")
    item_invalido = OportunidadeSync(titulo="Inválida", origem="A", tipo="B", link="http://bad.com")
    
    # mock_is_dado_valido retorna True para o primeiro e False para o segundo
    mock_is_dado_valido.side_effect = [True, False]
    
    lista_entrada = [item_valido, item_invalido]
    
    # Act
    resultado = filtrar_oportunidades_qualificadas(lista_entrada)
    
    # Assert
    assert len(resultado) == 1
    assert resultado[0].titulo == "Válida"
    assert mock_is_dado_valido.call_count == 2
