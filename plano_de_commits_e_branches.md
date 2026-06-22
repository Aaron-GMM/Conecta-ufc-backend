# Plano de Versionamento (Branches e Commits)

Este documento mapeia todas as alterações que realizamos no serviço de **Scrapings** e nos **Relatórios**, agrupando as mudanças em propostas lógicas de branches e commits. Isso garante um histórico de versionamento semântico, organizado e rastreável.

---

## 🌿 Branch 1: `feature/scrapings-unit-tests-coverage`
**Objetivo:** Isolar as atualizações no ambiente de testes e a melhoria da cobertura unitária do módulo de Scrapings.

* **Commit 1:** `build: add pytest and coverage dependencies via uv`
  * **O que foi feito:** Configuração do ambiente de testes no projeto `conecta-ufc-scrapings`, instalando as dependências `pytest`, `pytest-cov`, `pytest-asyncio`, `httpx` e `pytest-mock`.
  * **Arquivos Modificados:** `pyproject.toml`, `uv.lock`.

* **Commit 2:** `test: increase unit test coverage for scraper routes`
  * **O que foi feito:** Adição de testes unitários para validar cenários de resultados duplicados na mesma execução do scraper da UFC, e tratamento de editais/resultados que já existem no banco no scraper da FASTEF.
  * **Arquivos Modificados:** `conecta-ufc-scrapings/tests/api/test_scraper_routes.py`.

---

## 🌿 Branch 2: `feature/scrapings-integration-e2e-tests`
**Objetivo:** Criação do ambiente limpo para testes complexos (Integração e E2E) imitando a pirâmide de testes aplicada no Backend principal.

* **Commit 3:** `test: create integration tests suite for scrapings`
  * **O que foi feito:** Criação da estrutura de banco de dados SQLite em memória usando o `TestClient` injetado pelo FastAPI. Testes validam o preenchimento de Oportunidades, Resultados e o disparo do `SyncService` via HTTP, mockando apenas a ida à internet.
  * **Arquivos Modificados:** 
    * `conecta-ufc-scrapings/tests/integration/conftest.py`
    * `conecta-ufc-scrapings/tests/integration/test_integration_scrapings.py`
    * `conecta-ufc-scrapings/tests/integration/test_integration_api.py`

* **Commit 4:** `test: create end-to-end tests suite for scrapings`
  * **O que foi feito:** Criação da estrutura `tests/e2e/`, implementando validações estritas de "Caixa Preta" sem qualquer uso de Mocks contra as listagens da API de Scrapings e acionadores de automação em plano de fundo.
  * **Arquivos Modificados:** `conecta-ufc-scrapings/tests/e2e/test_e2e_scrapings.py`.

---

## 🌿 Branch 3: `docs/test-reports-and-mapping`
**Objetivo:** Consolidar e documentar todas as análises de testes e o planejamento de correção das falhas mapeadas, unindo contexto do Backend e Scraping.

* **Commit 5:** `docs: add integration and e2e test coverage reports for scrapings`
  * **O que foi feito:** Escrita da documentação formal atestando a cobertura de 96% e as metodologias aplicadas na integração e simulação ponta a ponta dos robôs.
  * **Arquivos Modificados:** 
    * `relatorio_cobertura_testes_scrapings_integracao.md`
    * `relatorio_cobertura_testes_scrapings_e2e.md`

* **Commit 6:** `docs: map coverage misses and propose solutions for backend and scrapings`
  * **O que foi feito:** Criação do artefato definitivo consolidando os *"Misses"* reportados nos seis relatórios gerados até o momento, contendo a proposta individual de solução em teste de código para alcançar 100%.
  * **Arquivos Modificados:** `mapeamento_misses_testes.md`

---
*Dica de Git Workflow: Estas branches podem ser criadas a partir da branch de desenvolvimento atual (`develop` ou `main`), commitadas individualmente e então submetidas como Pull Requests separadas.*
