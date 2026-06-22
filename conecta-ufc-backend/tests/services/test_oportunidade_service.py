import pytest
from unittest.mock import patch, MagicMock
from app.services.oportunidade_service import (
    informacao_ou_mensagem,
    resultado_response,
    oportunidade_response,
    listar_oportunidades_ordenadas,
    MENSAGEM_INFORMACAO_INDISPONIVEL
)

# --- Testes para informacao_ou_mensagem ---

class MockObject:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_informacao_ou_mensagem_campo_existente_com_valor_retorna_valor():
    # Arrange
    obj = MockObject(titulo="Bolsa Pesquisa")
    
    # Act
    resultado = informacao_ou_mensagem(obj, "titulo")
    
    # Assert
    assert resultado == "Bolsa Pesquisa"

def test_informacao_ou_mensagem_campo_inexistente_retorna_mensagem_padrao():
    # Arrange
    obj = MockObject()
    
    # Act
    resultado = informacao_ou_mensagem(obj, "campo_invisivel")
    
    # Assert
    assert resultado == MENSAGEM_INFORMACAO_INDISPONIVEL

def test_informacao_ou_mensagem_campo_nulo_retorna_mensagem_padrao():
    # Arrange
    obj = MockObject(titulo=None)
    
    # Act
    resultado = informacao_ou_mensagem(obj, "titulo")
    
    # Assert
    assert resultado == MENSAGEM_INFORMACAO_INDISPONIVEL

def test_informacao_ou_mensagem_campo_string_vazia_retorna_mensagem_padrao():
    # Arrange
    obj = MockObject(titulo="   ")
    
    # Act
    resultado = informacao_ou_mensagem(obj, "titulo")
    
    # Assert
    assert resultado == MENSAGEM_INFORMACAO_INDISPONIVEL

# --- Testes para resultado_response ---

def test_resultado_response_objeto_valido_retorna_dicionario_mapeado():
    # Arrange
    resultado_db = MockObject(
        id=1,
        titulo="Resultado Preliminar",
        link="http://link.com/resultado",
        data_publicacao="2026-06-20"
    )
    
    # Act
    resultado = resultado_response(resultado_db)
    
    # Assert
    assert resultado["id"] == 1
    assert resultado["titulo"] == "Resultado Preliminar"
    assert resultado["link"] == "http://link.com/resultado"
    assert resultado["data_publicacao"] == "2026-06-20"

def test_resultado_response_objeto_invalido_preenche_com_mensagem_padrao():
    # Arrange
    resultado_db = MockObject(
        id=2,
        titulo=None,
        link="",
        data_publicacao=None
    )
    
    # Act
    resultado = resultado_response(resultado_db)
    
    # Assert
    assert resultado["id"] == 2
    assert resultado["titulo"] == MENSAGEM_INFORMACAO_INDISPONIVEL
    assert resultado["link"] == MENSAGEM_INFORMACAO_INDISPONIVEL

# --- Testes para oportunidade_response ---

def test_oportunidade_response_com_resultados_retorna_dicionario_completo():
    # Arrange
    res1 = MockObject(id=10, titulo="Res 1", link="http://l.com", data_publicacao="2026-01-01")
    oportunidade_db = MockObject(
        id=1,
        titulo="Bolsa Extension",
        origem="UFC",
        tipo="Extensão",
        link="http://link.com",
        data_inicio="2026-02-01",
        data_fim="2026-12-01",
        remuneracao=700.0,
        vagas=1,
        data_criacao="2026-01-01",
        resultados=[res1]
    )
    
    # Act
    resultado = oportunidade_response(oportunidade_db)
    
    # Assert
    assert resultado["id"] == 1
    assert resultado["titulo"] == "Bolsa Extension"
    assert len(resultado["resultados"]) == 1
    assert resultado["resultados"][0]["titulo"] == "Res 1"

def test_oportunidade_response_sem_resultados_retorna_lista_vazia_em_resultados():
    # Arrange
    oportunidade_db = MockObject(
        id=2,
        titulo="Sem Resultados",
        origem="UFC",
        tipo="Ensino",
        link="http://abc.com",
        data_inicio=None,
        data_fim=None,
        remuneracao=None,
        vagas=None,
        data_criacao=None,
        resultados=None
    )
    
    # Act
    resultado = oportunidade_response(oportunidade_db)
    
    # Assert
    assert resultado["id"] == 2
    assert len(resultado["resultados"]) == 0
    assert resultado["vagas"] == MENSAGEM_INFORMACAO_INDISPONIVEL

# --- Testes para listar_oportunidades_ordenadas ---

def test_listar_oportunidades_ordenadas_db_vazio_retorna_lista_vazia():
    # Arrange
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_order = mock_options.order_by.return_value
    mock_order.all.return_value = []
    
    # Act
    resultado = listar_oportunidades_ordenadas(mock_session)
    
    # Assert
    assert resultado == []
    mock_session.query.assert_called_once()

def test_listar_oportunidades_ordenadas_db_com_dados_retorna_lista_mapeada():
    # Arrange
    op_db_1 = MockObject(
        id=1, titulo="Op 1", origem="UFC", tipo="Pesquisa", link="link1",
        data_inicio=None, data_fim=None, remuneracao=None, vagas=None, data_criacao=None, resultados=[]
    )
    mock_session = MagicMock()
    mock_query = mock_session.query.return_value
    mock_options = mock_query.options.return_value
    mock_order = mock_options.order_by.return_value
    mock_order.all.return_value = [op_db_1]
    
    # Act
    resultado = listar_oportunidades_ordenadas(mock_session)
    
    # Assert
    assert len(resultado) == 1
    assert resultado[0]["titulo"] == "Op 1"
