# Plano de Versionamento Backend (Branches e Commits)

Este documento lista e mapeia as alterações pendentes encontradas no repositório do **Backend**, organizando-as em uma estratégia semântica de branches e commits. Estas modificações contemplam as melhorias passadas relacionadas a qualidade de dados, tratamento de erros e a suíte completa de testes.

---

## 🌿 Branch 1: `feature/backend-data-quality`
**Objetivo:** Isolar o desenvolvimento do filtro de qualidade que recusa oportunidades com dados sujos ou links quebrados advindos dos scrapers.

* **Commit 1:** `feat: add data quality service and integrate it on sync route`
  * **O que contém:** Criação do serviço de verificação de qualidade (`data_quality.py`), adição da biblioteca `requests` no `requirements.txt` para pingar os links, e a integração deste filtro na rota `/internal/sync`.
  * **Arquivos Modificados:** 
    * `conecta-ufc-backend/app/services/data_quality.py` (Adicionado)
    * `conecta-ufc-backend/app/api/routes/internal.py` (Modificado)
    * `conecta-ufc-backend/requirements.txt` (Modificado)

---

## 🌿 Branch 2: `feature/backend-error-handling`
**Objetivo:** Organização do tratamento de exceções globais do FastAPI e pequenos reparos estruturais nos schemas do Pydantic.

* **Commit 2:** `feat: configure custom error handlers for the application`
  * **O que contém:** Criação do arquivo global de exceções customizadas para envelopar falhas do banco e validações e a integração da injeção dele no `main.py`.
  * **Arquivos Modificados:**
    * `conecta-ufc-backend/app/core/exceptions.py` (Adicionado)
    * `conecta-ufc-backend/app/main.py` (Modificado)

* **Commit 3:** `fix: update pydantic imports in favorito schema`
  * **O que contém:** Correção de importação deprecada do `ConfigDict` no schema de favoritos.
  * **Arquivos Modificados:**
    * `conecta-ufc-backend/app/schemas/favorito.py` (Modificado)

---

## 🌿 Branch 3: `feature/backend-test-suites`
**Objetivo:** Agrupar toda a suíte de pirâmide de testes do Backend (Unit, Integration e E2E) e sua documentação gerada.

* **Commit 4:** `test: add unit, integration, and e2e test suites`
  * **O que contém:** Toda a pasta recém-adicionada `tests/` com todos os *mockings* e configurações do SQLite injetadas no ambiente para bater 99% de cobertura.
  * **Arquivos Modificados:**
    * `conecta-ufc-backend/tests/` (Adicionado)

* **Commit 5:** `docs: add backend test coverage reports`
  * **O que contém:** Os relatórios em Markdown que atestam e analisam os índices de cobertura alcançados no backend principal em cada uma de suas camadas.
  * **Arquivos Modificados:**
    * `relatorio_cobertura_testes_backend.md` (Adicionado)
    * `relatorio_cobertura_testes_backend_e2e.md` (Adicionado)
    * `relatorio_cobertura_testes_backend_integracao.md` (Adicionado)

---
*Assim como os do serviço de scrapings, estas branches serão criadas a partir do estado da branch atual e podem ser enviadas à origem (GitHub) e submetidas como Pull Requests.*
