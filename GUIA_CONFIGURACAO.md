# 🚀 Guia de Configuração e Execução - Conecta-UFC

Este guia fornece instruções detalhadas para configurar, rodar e interagir com o ecossistema **Conecta-UFC**.

---

## 📋 Pré-requisitos
*   **Docker** e **Docker Compose** instalados.
*   **Python 3.12+** (caso deseje rodar fora do Docker).
*   Gerenciador de pacotes **uv** ou **pip**.

---

## ⚙️ Variáveis de Ambiente (.env)

O sistema utiliza arquivos `.env` para gerenciar configurações sensíveis e de infraestrutura.

### 1. Backend Core (`conecta-ufc-backend/.env`)
| Variável | Descrição | Valor Padrão (Dev) |
| :--- | :--- | :--- |
| `DATABASE_URL` | URL de conexão com o Postgres | `postgresql://conecta_user:conecta_password@postgres:5432/conecta_db` |
| `KEYCLOAK_SERVER_URL` | URL do servidor Keycloak | `http://conecta-keycloak:8080/` |
| `KEYCLOAK_REALM` | Realm configurado no Keycloak | `conecta-ufc` |
| `KEYCLOAK_CLIENT_ID` | ID do cliente para o backend | `conecta-ufc-backend` |
| `KEYCLOAK_CLIENT_SECRET` | Secret gerado pelo Keycloak | `conecta-ufc-dev-secret` |
| `SYNC_API_KEY` | Chave para autorizar sincronização | `conecta-ufc-dev-key` |

### 2. Scraping Worker (`conecta-ufc-scrapings/.env`)
| Variável | Descrição | Valor Padrão (Dev) |
| :--- | :--- | :--- |
| `SQLALCHEMY_DATABASE_URL` | Caminho do SQLite persistente | `sqlite:////app/data/conecta_ufc.db` |
| `CORE_API_URL` | Endpoint de sincronização do Core | `http://conecta-backend:8000/internal/sync` |
| `CORE_API_KEY` | Chave de sincronização (deve ser igual ao Core) | `conecta-ufc-dev-key` |

---

## 🛠️ Como Rodar (Docker Compose)

A maneira mais simples de subir toda a stack (Postgres, Keycloak, Backend, Worker) é usando o Docker Compose:

```bash
# Na raiz do projeto
docker compose up -d --build
```

### Verificação de Saúde
*   **Keycloak:** [http://localhost:8080](http://localhost:8080) (Admin: `admin`/`admin`)
*   **Backend Core:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Scraping API:** [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 📡 Catálogo de Rotas (Endpoints)

### 1. Núcleo Central (`conecta-ufc-backend`) - Porta 8000

#### Autenticação e Usuários (`/usuarios`)
*   `POST /usuarios`: Cadastra um novo usuário no sistema e no Keycloak.
*   `POST /usuarios/login`: Realiza o login e retorna o `access_token` JWT.

#### Oportunidades (`/oportunidades`)
*   `GET /oportunidades`: Lista todas as oportunidades sincronizadas no banco central.

#### Interno / Sincronização (`/internal`)
*   `POST /internal/sync`: **[PROTEGIDO]** Recebe dados do Worker. Requer header `X-Sync-Key`.

---

### 2. Worker de Coleta (`conecta-ufc-scrapings`) - Porta 8001

#### Gerenciamento de Oportunidades (`/api/oportunidades`)
*   `GET /api/oportunidades`: Lista as vagas coletadas localmente (paginado).

#### Controle de Scrapers (`/api/scrapers`)
*   `POST /api/scrapers/ufc/run`: Dispara manualmente o scraper da UFC Quixadá.
*   `POST /api/scrapers/fastef/run`: Dispara manualmente o scraper da FASTEF (inclui análise de PDFs).
*   `POST /api/scrapers/sync`: Dispara manualmente a sincronização dos dados locais para o Backend Core.

---

## ⏱️ Automação (Scheduler)

O Worker possui um **Background Scheduler (APScheduler)** configurado para manter os dados sempre atualizados sem intervenção manual.

*   **Ciclo:** A cada 6 horas.
*   **Fluxo:**
    1.  Executa `UfcScraper`.
    2.  Executa `FastefScraper`.
    3.  Executa `SyncService` (envia as novidades para o Core).

---

## 📦 Estrutura de Pastas

```text
.
├── conecta-ufc-backend/    # API Central (FastAPI + Postgres)
├── conecta-ufc-scrapings/  # Worker (FastAPI + SQLite + Scrapers)
├── docker/                 # Configurações de infra (Keycloak JSON)
├── docker-compose.yml      # Orquestrador da stack
└── ARQUITETURA.md          # Documentação técnica profunda
```

---

## 🛠️ Troubleshooting (Resolução de Problemas)

### Erro: "sqlite3.OperationalError: unable to open database file"
Certifique-se de que a pasta `conecta-ufc-scrapings/data` existe e possui permissões de escrita. No Linux:
```bash
chmod -R 777 conecta-ufc-scrapings/data
```

### Migrações de Banco de Dados
Caso altere modelos, use o Alembic dentro dos containers:
```bash
docker exec -it conecta-scrapings alembic revision --autogenerate -m "nome"
docker exec -it conecta-scrapings alembic upgrade head
```
