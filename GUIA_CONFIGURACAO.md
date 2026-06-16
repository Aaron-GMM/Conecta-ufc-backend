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

O `docker-compose.yml` ja define valores padrao de desenvolvimento para a comunicacao entre Backend, Keycloak, Postgres e Worker.
Arquivos `.env` continuam opcionais para sobrescrever configuracoes locais, mas nao sao obrigatorios para subir a stack de desenvolvimento.
O Postgres nao e publicado na porta do host; ele fica disponivel apenas como `postgres:5432` dentro da rede do Compose para evitar colisao com bancos locais da maquina.

### Verificação de Saúde
*   **Keycloak:** [http://localhost:8080](http://localhost:8080) (Admin: `admin`/`admin`)
*   **Caixa de email local:** [http://localhost:8025](http://localhost:8025)
*   **Backend Core:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Scraping API:** [http://localhost:8001/docs](http://localhost:8001/docs)

O Keycloak e importado com SMTP apontando para o container `mailpit`.
Isso permite testar recuperacao de senha localmente sem configurar Gmail, SendGrid ou outro provedor externo.
Se o volume do Keycloak ja existir, rode `docker compose down -v` e depois `docker compose up -d --build` para importar novamente o realm com essa configuracao.

---

## 📡 Catálogo de Rotas (Endpoints)

### 1. Núcleo Central (`conecta-ufc-backend`) - Porta 8000

#### Autenticação e Usuários (`/usuarios`)
*   `POST /usuarios`: Cadastra um novo usuário no sistema e no Keycloak.
*   `POST /usuarios/login`: Realiza o login e retorna o `access_token` JWT.
*   `POST /usuarios/esqueci-senha`: Pede ao Keycloak para enviar o email de redefinicao de senha.

#### Oportunidades (`/oportunidades`)
*   `GET /oportunidades`: Lista oportunidades com suporte a paginação e filtros (`busca`, `origem`, `tipo`).
*   `POST /oportunidades/{id}/favoritar`: **[AUTENTICADO]** Adiciona uma oportunidade aos favoritos do usuário.
*   `DELETE /oportunidades/{id}/favoritar`: **[AUTENTICADO]** Remove uma oportunidade dos favoritos.
*   `GET /oportunidades/favoritos`: **[AUTENTICADO]** Lista todas as oportunidades favoritadas pelo usuário logado.

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

---

## 🧪 Guia de Testes (MVP)

Este guia detalha como validar as funcionalidades principais do sistema utilizando `cURL` e como explorar a API via documentação interativa (Swagger).

### 1. Testando via cURL (Passo a Passo)

#### A. Fluxo de Oportunidades (Público)

1.  **Listagem Paginada:**
    ```bash
    curl -s -X GET "http://localhost:8000/oportunidades?page=1&size=5" | python3 -m json.tool
    ```

2.  **Busca por Título:**
    ```bash
    curl -s -X GET "http://localhost:8000/oportunidades?busca=Monitoria" | python3 -m json.tool
    ```

3.  **Filtragem por Origem e Tipo:**
    ```bash
    curl -s -X GET "http://localhost:8000/oportunidades?origem=UFC-Quixad%C3%A1&tipo=PID" | python3 -m json.tool
    ```

#### B. Fluxo de Usuário e Favoritos (Autenticado)

1.  **Criar um Usuário:**
    ```bash
    curl -s -X POST "http://localhost:8000/usuarios" \
         -H "Content-Type: application/json" \
         -d '{
               "nome": "Aluno Teste",
               "email": "aluno.teste@example.com",
               "senha": "password123",
               "curso": "Engenharia de Software",
               "oportunidades": ["Estágio"]
             }'
    ```

2.  **Fazer Login (Obter Token):**
    ```bash
    # O comando abaixo extrai apenas o token do JSON de resposta
    TOKEN=$(curl -s -X POST "http://localhost:8000/usuarios/login" \
         -H "Content-Type: application/json" \
         -d '{"email": "aluno.teste@example.com", "senha": "password123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "Seu Token: $TOKEN"
    ```

3.  **Favoritar uma Oportunidade (Ex: ID 211):**
    ```bash
    curl -s -X POST "http://localhost:8000/oportunidades/211/favoritar" \
         -H "Authorization: Bearer $TOKEN"
    ```

4.  **Listar Meus Favoritos:**
    ```bash
    curl -s -X GET "http://localhost:8000/oportunidades/favoritos" \
         -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
    ```

### 2. Testando via Swagger (Interface Web)

1.  Acesse: `http://localhost:8000/docs`.
2.  Para rotas protegidas (Favoritos):
    *   Primeiro, use o endpoint `POST /usuarios/login` para obter o token.
    *   Copie o valor de `access_token`.
    *   No topo da página, clique no botão **"Authorize"** (ícone de cadeado).
    *   Cole o token no campo e clique em **"Authorize"**.
    *   Agora você pode testar os endpoints de favoritos diretamente na interface.
