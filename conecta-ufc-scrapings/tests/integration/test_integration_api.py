import pytest
from app.models.oportunidade import OportunidadeDB, ResultadoDB

def test_integration_listar_oportunidades_vazio(client):
    response = client.get("/api/oportunidades/")
    assert response.status_code == 200
    assert response.json()["data"] == []

def test_integration_listar_oportunidades_com_dados(client, db_session):
    nova_vaga = OportunidadeDB(titulo="Vaga de Integração", origem="UFC", tipo="Estágio", link="http://integ")
    db_session.add(nova_vaga)
    db_session.commit()

    response = client.get("/api/oportunidades/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["titulo"] == "Vaga de Integração"

def test_integration_listar_resultados_vazio(client):
    response = client.get("/api/resultados/")
    assert response.status_code == 200
    assert response.json()["data"] == []

def test_integration_listar_resultados_com_dados(client, db_session):
    nova_vaga = OportunidadeDB(titulo="Vaga de Integração 2", origem="UFC", tipo="Bolsa", link="http://integ2")
    db_session.add(nova_vaga)
    db_session.commit()
    
    novo_res = ResultadoDB(titulo="Resultado Int", link="http://res", oportunidade_id=nova_vaga.id)
    db_session.add(novo_res)
    db_session.commit()

    response = client.get("/api/resultados/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["titulo"] == "Resultado Int"
