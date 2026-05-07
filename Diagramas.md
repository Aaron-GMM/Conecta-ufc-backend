
# Documentação de Arquitetura: Projeto Conecta-UFC

## 1. Visão Geral do Projeto
O **Conecta-UFC** é um sistema distribuído projetado para centralizar, monitorar e disponibilizar oportunidades acadêmicas e profissionais (bolsas, projetos de extensão, processos seletivos) da Universidade Federal do Ceará. O sistema utiliza técnicas de *web scraping* para extrair dados de fontes institucionais como o Campus Quixadá e a FASTEF, normalizando essas informações para consumo via API por interfaces Web e Mobile.

---

## 2. Motivações e Escolhas Tecnológicas
A *stack* tecnológica foi selecionada com foco em performance, escalabilidade e robustez no tratamento de dados externos.

* **Linguagem Python 3.12:** Escolhida por sua maturidade em processamento de dados e vasta biblioteca para *scraping* (BeautifulSoup4) e APIs web.
* **FastAPI:** Framework moderno de alta performance que utiliza programação assíncrona, essencial para lidar com múltiplas requisições de entrada de dados e consultas externas.
* **Pydantic:** Utilizado para garantir a integridade dos dados através de validação rigorosa e tipagem, protegendo o sistema contra vulnerabilidades como *XSS* e garantindo contratos de API consistentes.
* **SQLAlchemy & Alembic:** O ORM SQLAlchemy permite uma manipulação de dados independente do banco de dados físico, enquanto o Alembic gerencia migrações de esquema de forma versionada e segura.
* **PostgreSQL (Core):** Escolhido para o servidor central pela sua capacidade de lidar com alta concorrência e integridade referencial complexa em produção.
* **SQLite (Worker):** Utilizado localmente no Worker como uma *Staging Area* (área de triagem). Sua simplicidade permite que o Worker opere de forma isolada e resiliente a falhas de rede.

---

## 3. Arquitetura e Diagramas

### 3.1. Arquitetura de Alto Nível (Distribuição de Serviços)
A solução adota o padrão **Store and Forward** (Armazenar e Encaminhar), separando a coleta de dados da sua exposição pública.

```mermaid
graph LR
    subgraph Internet
        UFC[Site UFC Quixadá]
        FASTEF[Site FASTEF]
    end

    subgraph "Worker (conecta-ufc-scrapings)"
        Scraper[Motores de Busca / BS4]
        SQLite[(SQLite - Staging)]
        Sync[Script de Sincronização]
        
        UFC --> Scraper
        FASTEF --> Scraper
        Scraper --> SQLite
        SQLite --> Sync
    end

    subgraph "Core (conecta-ufc-backend)"
        Ingestão[API Ingestão: /api/internal/sync]
        Postgres[(PostgreSQL - Produção)]
        PublicAPI[API Externa: /api/oportunidades]
        
        Sync -- "POST (JSON + API Key)" --> Ingestão
        Ingestão --> Postgres
        Postgres --> PublicAPI
    end

    PublicAPI --> FE[Frontend / Mobile]
```



**Explicação:** O **Worker** atua de forma autônoma, raspando os sites e salvando os achados no **SQLite** local. Um script de sincronização posterior envia esses dados via `POST` para o **Core Backend**, que os persiste definitivamente no **PostgreSQL**. Isso garante que, se o site da UFC estiver instável, o Worker não interrompe o funcionamento do Backend central.

---

### 3.2. Padrão de Projeto: Camadas Internas
O Backend segue a separação estrita entre controladores e entidades, garantindo que a lógica de negócio não seja acoplada diretamente à interface de rede ou ao banco de dados.

```mermaid
graph TD
    %% Entrada
    Client((Cliente / Frontend / Worker)) --> Router

    subgraph "Camada de API (FastAPI)"
        Router["Controladores / Endpoints (Rotas e Métodos HTTP)"]
        Schema["Pydantic Schemas / DTOs (Validação e Serialização)"]
    end

    subgraph "Camada de Negócio (Service Layer)"
        Service["Serviços / Lógica de Domínio (Regras e Algoritmo Two-Pass)"]
    end

    subgraph "Camada de Dados (Persistence Layer)"
        ORM["SQLAlchemy Models / Entities (Mapeamento Relacional)"]
        Session["DB Session (Gerenciamento de Conexão)"]
    end

    %% Fluxo de Dados
    Router --> Schema
    Schema --> Service
    Service --> ORM
    ORM --> Session
    
    %% Destinos
    subgraph "Bancos de Dados"
        PG[(PostgreSQL - Core)]
        SL[(SQLite - Worker)]
    end

    Session --> PG
    Session --> SL
```



---

### 3.3. Modelo de Domínio e Persistência (DER)
O banco de dados foi modelado para suportar a relação de um Edital para múltiplos Resultados e Aditivos.

```mermaid
erDiagram
    OPORTUNIDADES ||--o{ RESULTADOS : "possui"

    OPORTUNIDADES {
        int id PK
        string titulo
        string origem
        string tipo
        string link
        string datas
    }

    RESULTADOS {
        int id PK
        string titulo
        string link
        int oportunidade_id FK
    }
```



**Explicação:** A tabela `oportunidades` armazena o edital principal. A tabela `resultados` está vinculada a ela via chave estrangeira, permitindo que cada oportunidade exiba seu histórico completo de atualizações.

---

### 3.4. Fluxograma do Algoritmo de Scraping (Diferencial Técnico)
Para lidar com a desorganização das fontes externas (especialmente na FASTEF), foi implementado um **Algoritmo de Duas Passadas**.

```mermaid
flowchart TD
    Start((Início)) --> Req[Requisição HTTP via BaseScraper]
    Req --> Raw[Extração de Dados Brutos / BS4]
    Raw --> Loop{Para cada item encontrado}
    
    Loop --> Type{O item é Edital ou Resultado?}
    
    %% Fluxo de Edital
    Type -- "Edital (Oportunidade)" --> SaveOp[Salvar na tabela 'oportunidades']
    SaveOp --> Next
    
    %% Fluxo de Resultado
    Type -- "Resultado / Aditivo" --> Regex[Buscar Edital Pai via Regex]
    Regex --> Found{Pai encontrado no DB?}
    
    Found -- Sim --> Link[Vincular ao oportunidade_id existente]
    Found -- Não --> Ghost[Criar 'Ghost Parent' / Pai Provisório]
    
    Link --> SaveRes[Salvar na tabela 'resultados']
    Ghost --> Link
    SaveRes --> Next
    
    Next[Próximo Item] --> Loop
    Loop -- Fim da Lista --> End((Fim: Dados Normalizados no SQLite))
```



**Solução Inovadora:** O uso do padrão **Ghost Parent** resolve o problema de integridade referencial quando um resultado é publicado, mas o edital original já foi removido do site de origem. O sistema cria um "Pai Provisório" para garantir que o resultado não seja perdido.

---

### 3.5. Ciclo de Vida da Sincronização (Diagrama de Sequência)
Este diagrama detalha a comunicação temporal entre o Worker e a API central.

```mermaid
sequenceDiagram
    participant W as Worker (Scraper)
    participant DB_L as SQLite (Local)
    participant S as Sync Script
    participant API as Core API (Backend)
    participant DB_C as PostgreSQL (Central)

    Note over W, DB_L: 1. Processo de Raspagem
    W->>W: Executa Scraping (Two-Pass)
    W->>DB_L: Salva Oportunidades/Resultados (sincronizado=False)
    
    Note over S, API: 2. Processo de Sincronização
    S->>DB_L: Busca registros onde sincronizado = False
    DB_L-->>S: Retorna dados em JSON
    
    S->>API: POST /api/internal/sync (JSON + API Key)
    API->>API: Valida Schemas (Pydantic)
    API->>DB_C: Persiste dados de forma definitiva
    DB_C-->>API: Sucesso na gravação
    API-->>S: Resposta HTTP 200 OK
    
    Note over S, DB_L: 3. Atualização de Status
    S->>DB_L: Update: set sincronizado = True
    DB_L-->>S: Confirmação
```



---

## 4. Segurança e Integridade
* **Ingestão Protegida:** A rota `/api/internal/sync` é protegida por uma chave de API para evitar inserções de dados por terceiros não autorizados.
* **Flag de Sincronização:** O uso da coluna `sincronizado_backend` no SQLite garante que, em caso de queda de internet, o Worker reenvie apenas os dados pendentes no próximo ciclo.

---

## 5. Próximos Passos (Backlog)
1.  Migração completa dos modelos para o ambiente de produção PostgreSQL.
2.  Implementação do `APScheduler` para automatização dos ciclos de busca.
3.  Conteinerização de toda a stack utilizando Docker e Docker Compose.