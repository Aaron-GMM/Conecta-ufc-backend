import pytest
from app.models.oportunidade import OportunidadeDB, ResultadoDB
import os

@pytest.fixture
def override_sync_key(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "sync_api_key", "chave_secreta_teste")
    yield "chave_secreta_teste"

# --- Testes de Integração para Internal (Sync) ---

def test_integration_internal_sync_sem_chave_retorna_403(client):
    response = client.post("/internal/sync", json=[])
    assert response.status_code == 403
    assert "inválida" in response.json()["mensagem"].lower()

def test_integration_internal_sync_chave_invalida_retorna_403(client, override_sync_key):
    headers = {"X-Sync-Key": "chave_errada"}
    response = client.post("/internal/sync", json=[], headers=headers)
    assert response.status_code == 403

def test_integration_internal_sync_payload_vazio_retorna_200_com_0_registros(client, override_sync_key):
    headers = {"X-Sync-Key": override_sync_key}
    response = client.post("/internal/sync", json=[], headers=headers)
    assert response.status_code == 200
    assert response.json()["oportunidades_recebidas"] == 0

def test_integration_internal_sync_cria_novas_oportunidades_e_resultados(client, db_session, override_sync_key, monkeypatch):
    import app.api.routes.internal as router_internal
    
    # Mockando a função do módulo importado no roteador!
    monkeypatch.setattr(router_internal, "filtrar_oportunidades_qualificadas", lambda ops: ops)

    headers = {"X-Sync-Key": override_sync_key}
    payload = [
        {
            "titulo": "Bolsa A",
            "origem": "UFC",
            "tipo": "Bolsa",
            "link": "http://bolsa-a",
            "resultados": [
                {"titulo": "Resultado Bolsa A", "link": "http://res-a"}
            ]
        },
        {
            "titulo": "Bolsa B",
            "origem": "FASTEF",
            "tipo": "PIBC",
            "link": "http://bolsa-b",
            "resultados": []
        }
    ]

    response = client.post("/internal/sync", json=payload, headers=headers)
    assert response.status_code == 200
    dados = response.json()
    assert dados["oportunidades_novas"] == 2
    assert dados["resultados_novos"] == 1

    # Verifica o banco
    vagas = db_session.query(OportunidadeDB).all()
    assert len(vagas) == 2
    resultados = db_session.query(ResultadoDB).all()
    assert len(resultados) == 1

def test_integration_internal_sync_ignora_oportunidades_existentes_mas_atualiza_resultados(client, db_session, override_sync_key, monkeypatch):
    import app.api.routes.internal as router_internal
    monkeypatch.setattr(router_internal, "filtrar_oportunidades_qualificadas", lambda ops: ops)

    # Arrange: insere uma vaga no banco com resultados
    vaga_existente = OportunidadeDB(titulo="Bolsa Antiga", origem="UFC", tipo="Bolsa", link="http://mesmo-link")
    db_session.add(vaga_existente)
    db_session.commit()

    headers = {"X-Sync-Key": override_sync_key}
    payload = [
        {
            "titulo": "Bolsa Atualizada", # Titulo mudou, mas link é igual, vai ignorar a atualização da vaga
            "origem": "UFC",
            "tipo": "Bolsa",
            "link": "http://mesmo-link",
            "remuneracao": 500.0,
            "resultados": [
                {"titulo": "Novo Resultado", "link": "http://novo-res"}
            ]
        }
    ]

    # Act
    response = client.post("/internal/sync", json=payload, headers=headers)
    
    # Assert
    assert response.status_code == 200
    dados = response.json()
    assert dados["oportunidades_novas"] == 0
    assert dados["resultados_novos"] == 1
    
    # Verifica que não foi atualizada
    db_session.refresh(vaga_existente)
    assert vaga_existente.titulo == "Bolsa Antiga" # não atualiza
    assert vaga_existente.remuneracao is None # não atualiza
    
    # Mas o resultado foi criado
    res = db_session.query(ResultadoDB).filter_by(oportunidade_id=vaga_existente.id).first()
    assert res is not None
    assert res.titulo == "Novo Resultado"
