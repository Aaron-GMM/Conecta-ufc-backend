# Relatório de Auditoria e Planejamento de Sprints - Conecta-UFC

Este documento apresenta o estado atual do ecossistema **Conecta-UFC**, o mapeamento de requisitos em relação à implementação e o cronograma de atividades para as próximas Sprints.

---

## 1. Auditoria de Funcionalidades (Estado Atual)

O projeto possui uma base sólida de coleta e autenticação, mas a "ponte" de integração e a persistência central ainda precisam ser consolidadas.

| Categoria | Funcionalidade | Estado Atual |
| :--- | :--- | :--- |
| **Autenticação** | Cadastro e Login integrados ao Keycloak | ✅ Concluído |
| **Autenticação** | Emissão e Gerenciamento de Tokens (JWT) | ✅ Concluído |
| **Coleta** | Scraper UFC Quixadá e FASTEF | ✅ Concluído |
| **Coleta** | Algoritmo Two-Pass e Padrão Ghost Parent | ✅ Concluído |
| **Coleta** | Parser de PDF (Extração de Vagas, Datas e R$) | ✅ Concluído |
| **Integração** | Sincronização Worker (SQLite) ➔ Backend (Postgres) | ❌ Pendente |
| **Persistência** | Banco de Dados Central (PostgreSQL) | ❌ Pendente |
| **API Central** | Endpoints de Listagem e Filtros | ❌ Pendente |
| **Usuário** | Sistema de Favoritos e Alertas | ❌ Pendente |
| **Automação** | Agendamento de Tarefas (APScheduler) | ❌ Pendente |

---

## 2. Mapeamento de Requisitos e Lacunas

O sistema opera sob o padrão **Store and Forward**. Abaixo, mapeamos o que falta para completar este ciclo:

1.  **Backend Central (`conecta-ufc-backend`):** Atualmente funciona como um provedor de autenticação. É necessário configurar a infraestrutura de dados (Postgres + SQLAlchemy) e portar os modelos de oportunidades.
2.  **Sincronização:** O Worker precisa de um mecanismo para "empurrar" os dados locais para a API central de forma segura.
3.  **Segurança de Consumo:** Implementar a validação do Token JWT nas rotas de consumo de dados.

---

## 3. Cronograma de Desenvolvimento

O projeto será finalizado seguindo a divisão estratégica entre funcionalidades e validação.

### 🚀 Sprint 2: Desenvolvimento de Funcionalidades (Foco em Entrega)
O objetivo desta sprint é garantir que todas as regras de negócio e fluxos de dados estejam operacionais.

*   **Atividade 2.1: Estruturação do Cofre Central**
    *   Configuração do PostgreSQL e SQLAlchemy no Backend.
    *   Criação de Models e Schemas (Oportunidades e Resultados).
    *   Configuração do Alembic para migrações no ambiente de produção.
*   **Atividade 2.2: Implementação da Integração Distribuída**
    *   Criação da rota `POST /api/internal/sync` no Backend.
    *   Desenvolvimento do script de sincronização no Worker.
    *   Implementação do `APScheduler` para automação do ciclo de busca.
*   **Atividade 2.3: Experiência do Usuário (API)**
    *   Endpoint de listagem com filtros avançados (Busca, Origem, Tipo).
    *   Gerenciamento de Perfil: Criar endpoints `GET /usuarios/me` e `PATCH /usuarios/me` para retornar dados do usuário (necessário para exibição de iniciais no frontend) e permitir edição de curso/interesses.
    *   Lógica de "Favoritar" vinculada ao ID do Keycloak.

### 🧪 Sprint 3: Testes, Refinamento e E2E
Foco total em qualidade, estabilidade e conformidade com os requisitos de software.

*   **Testes Unitários:**
    *   Validação dos Scrapers (HTML/PDF) contra mudanças estruturais.
    *   Testes de lógica de negócio e validação de schemas Pydantic.
*   **Testes de Integração e E2E:**
    *   Simulação do fluxo completo: Raspagem ➔ SQLite ➔ Sync ➔ Postgres ➔ API.
    *   Validação de segurança: Testar se rotas protegidas rejeitam tokens inválidos.
*   **Polimento e Performance:**
    *   Correção de pequenos erros de lógica ou fluxos identificados nos testes.
    *   Otimização de queries SQL e limpeza de código.

---

## 4. Próximos Passos Imediatos

A equipe técnica focará agora na **Atividade 2.1**, iniciando a configuração do banco de dados central no `conecta-ufc-backend` para permitir a recepção dos dados coletados pelos Workers.
