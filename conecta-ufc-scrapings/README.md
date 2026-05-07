# CONTEXTO DE SISTEMA: BACKEND E WEB SCRAPERS (PROJETO CONECTA-UFC)

**Instrução Inicial para o LLM:** A partir de agora, você atuará como o Engenheiro de Software Backend Sênior deste projeto. Use este documento como sua única fonte de verdade sobre a arquitetura, estado atual do código e requisitos pendentes para as próximas tarefas que eu solicitar.

---

## 1. Visão Geral e Stack Tecnológico
O **Conecta-UFC** é uma API RESTful cujo núcleo de negócio depende fortemente de extração de dados automatizada (Web Scraping). O objetivo é buscar, padronizar e fornecer via API editais e vagas de bolsas acadêmicas (PID, PIBIC, P&D) da Universidade Federal do Ceará e fundações anexas (ex: Fastef, Insight Lab).

* **Framework Web:** FastAPI (Python 3.x)
* **Banco de Dados:** PostgreSQL (via SQLAlchemy)
* **Migrações:** Alembic
* **Validação de Dados:** Pydantic
* **Web Scraping:** `requests` para requisições HTTP e `BeautifulSoup4` (a definir) para parsing.

---

## 2. Estado Atual do Repositório (O que já temos codificado)
A infraestrutura base foi iniciada, mas a lógica de negócio ainda está vazia.

### 2.1. Estrutura de Banco de Dados (ORM)
* **`app/db/database.py`:** Configuração da engine do SQLAlchemy e controle de sessão.
* **`alembic/versions/fb7001220436_tabelas_iniciais.py`:** Migração inicial com as tabelas base já criadas no SGBD.
* **`app/models/oportunidade.py`:** Modelo SQLAlchemy mapeando a entidade principal (Vaga/Edital).
* **`app/schemas/oportunidade.py`:** Schemas Pydantic (`OportunidadeCreate`, `OportunidadeResponse`) para validação de payload.

### 2.2. Web Scraping (Base)
* **`app/scrapers/base_scraper.py`:** Contém a classe abstrata/mãe. Atualmente ela possui **apenas** o método para fazer requisições HTTP (`fetch_html`) com tratativa de erros e *retries*. **Atenção:** Ela ainda não faz nenhum *parsing* de HTML.
* **`paginas/fastef-pagina-processo-seletivo.html`:** Um mock (código-fonte salvo localmente) de uma página da Fastef para ser usado na criação e teste dos extratores sem precisar bater no servidor real durante o desenvolvimento.

### 2.3. Arquivos Vazios/Incompletos
* **`app/main.py` e `main.py` (raiz):** Estão praticamente vazios (código gerado pela IDE). Não há instâncias ativas do `FastAPI()`, tampouco roteamento (routers) configurado.

---

## 3. Requisitos Pendentes (O que precisa ser desenvolvido)
Ao criar novas lógicas, você deve seguir estritamente as Regras de Negócio (RN) e Requisitos Funcionais (RF) abaixo.

### 3.1. Requisitos da API (FastAPI)
* **[RF01/RF02] Listagem e Filtros:** Criar o endpoint `GET /oportunidades`. Ele deve obrigatoriamente aceitar *query parameters* para filtros cumulativos de:
    * `categoria` (ex: PID, PET, P&D, Monitoria)
    * `nivel` (ex: Graduação, Pós-Graduação)
    * `curso` (ex: Engenharia de Software, Design) -> *Nota: Este filtro foi apontado como o mais crítico na pesquisa de usuários.*
* **[RF07/RF08] Painel Admin:** * Criar sistema de autenticação JWT (`POST /login`).
    * Criar rotas protegidas `PUT /oportunidades/{id}` e `DELETE /oportunidades/{id}` para curadoria humana (permitir que o admin corrija um link de inscrição que o scraper pegou errado ou aprove uma vaga).
* **[RF10] Encerramento Automático:** Rota ou rotina interna que compare a `data_encerramento` da vaga com a data atual (`datetime.now()`) e atualize o `status` no banco para "Encerrada".

### 3.2. Requisitos dos Scrapers
* **[RF09] Scrapers Específicos:** Criar classes filhas de `BaseScraper` (ex: `UfcScraper`, `FastefScraper`). Estas classes devem receber o HTML bruto, processá-lo (via BeautifulSoup ou lxml) e retornar objetos baseados nos schemas do Pydantic (`OportunidadeCreate`).
* **Dados Alvo:** O scraper deve tentar extrair, no mínimo: *Título, Órgão ofertante, Valor da bolsa, Prazo de inscrição, Nível, Requisitos e o Link de inscrição original*.
* **[RF11] Captura de Resultados:** Um scraper específico (ou método) para capturar publicações de "Resultados" (PDFs/Links) e realizar um *UPDATE* na entidade da Vaga correspondente, vinculando o resultado ao edital pai.

### 3.3. Automação de Tarefas (Background Jobs)
* **Orquestração:** O sistema deve executar os robôs autonomamente 1x ao dia. Precisaremos definir/implementar um agendador (ex: `APScheduler` rodando junto ao FastAPI ou rotina em `Celery`/`RabbitMQ`).

---

## 4. Diretrizes de Código
Sempre que você for gerar código para este projeto, siga estas regras:
1.  **Modularização:** Não crie arquivos monolíticos. Separe a lógica em pastas coerentes (`app/api/routes`, `app/core`, `app/services/scrapers`).
2.  **Injeção de Dependências (DI):** Use a DI do FastAPI (`Depends`) para instanciar conexões de banco de dados (`get_db`).
3.  **Resiliência:** Os scrapers devem usar blocos `try/except` robustos. Se o layout de um site (ex: Fastef) mudar, o scraper daquele site deve falhar graciosamente e logar o erro, sem derrubar a API ou o script de automação inteiro.
4.  **Tipagem:** Use Type Hints rigorosos do Python 3 em todas as funções.

**Aguardando seu primeiro comando...**