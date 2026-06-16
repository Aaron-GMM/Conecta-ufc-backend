# Conecta-UFC: Sistema Distribuído de Agregação de Oportunidades

O **Conecta-UFC** é uma plataforma de alta disponibilidade projetada para centralizar e normalizar a oferta de oportunidades acadêmicas e profissionais (bolsas de fomento, monitorias, extensões e editais de pesquisa) da Universidade Federal do Ceará.

O ecossistema opera sob o padrão **Store and Forward**, desacoplando a fase crítica de extração de dados (*Edge Data Collection*) da camada de entrega e serviços (*Centralized API*).

---

## 👥 Equipe
*   **Aaron Gibran** ([@Aaron-GMM](https://github.com/Aaron-GMM))
*   **Daniel Jacó** ([@Daniel-jacodev](https://github.com/Daniel-jacodev))
*   **Sabrina Damasceno** ([@SabrinaDamascenoDev](https://github.com/SabrinaDamascenoDev))

---

## 🔗 Ferramentas Externas
*   **[Notion - Gestão e Requisitos](https://app.notion.com/p/ConectaUFC-Documenta-o-36336e3d1225803cb9e7d4cecb25b3b9):** Centralização de toda a documentação, backlog e acompanhamento de tarefas.
*   **[Figma - Prototipação](https://www.figma.com/design/81oE8ByfTje6hoOWlzrSoI/Conecta-UFC?node-id=0-1&p=f&t=Ou7BDXSjktoAt3Ej-0):** Protótipo de alta fidelidade das interfaces Web e Mobile.

---

## 📂 Documentação e Artefatos
*   **[Documento de Arquitetura](./ARQUITETURA.md):** Detalhamento técnico, diagramas Mermaid (DER, Fluxos, Sequência) e justificativa tecnológica.
*   **[Apresentação de Artefatos](./ARTEFATOS.md):** Resumo de tudo que foi desenvolvido (Scrapers, API, Banco de Dados, UI).
*   **[Guia de Configuração e Execução](./GUIA_CONFIGURACAO.md):** Passo a passo detalhado para rodar o projeto, variáveis de ambiente e catálogo de rotas.
*   **[Auditoria e Planejamento](./RELATORIO_PLANEJAMENTO.md):** Relatório de estado atual e planejamento das próximas entregas.

---

## 🏗️ Estrutura do Repositório

O projeto é dividido em dois grandes subsistemas:

### 1. [Serviço de Coleta (`conecta-ufc-scrapings`)](./conecta-ufc-scrapings/)
*   Engine de extração baseada em BeautifulSoup4.
*   Persistência de Staging em **SQLite**.
*   Algoritmos de normalização de dados e vinculação de editais.

### 2. [Núcleo de Processamento (`conecta-ufc-backend`)](./conecta-ufc-backend/)
*   API RESTful desenvolvida em **FastAPI**.
*   Persistência definitiva em **PostgreSQL**.
*   Integração com **Keycloak** para autenticação robusta.

---

## 🛠️ Stack Tecnológica

| Tecnologia | Finalidade |
| :--- | :--- |
| **Python 3.12** | Linguagem principal do ecossistema |
| **FastAPI** | Framework para API Assíncrona |
| **PostgreSQL** | Banco de dados relacional de produção |
| **SQLite** | Banco de dados local para o Worker |
| **Keycloak** | Gestão de identidade e acesso (IAM) |
| **Docker** | Orquestração de containers e infraestrutura |

---

## 🚀 Como Rodar o Projeto Localmente

Consulte as instruções de configuração do ambiente no README de cada subsistema ou utilize o Docker Compose na raiz:

```bash
docker compose up -d
```

O `docker-compose.yml` ja possui valores padrao de desenvolvimento para backend, worker, Postgres e Keycloak. Arquivos `.env` locais continuam opcionais para ajustes especificos.
O Postgres fica acessivel apenas na rede interna do Docker, o que evita conflito com um banco ja rodando na maquina.

O painel do Keycloak estará disponível em `http://localhost:8080`.
A caixa de entrada local para emails do Keycloak estará disponível em `http://localhost:8025`.
A documentação interativa da API (Swagger) poderá ser acessada em `http://localhost:8000/docs`.

O email de redefinicao de senha usa o client publico `conecta-ufc-frontend` e redireciona de volta para `http://localhost:5173/login`.

Para um passo a passo de como validar as funcionalidades, consulte o [**Guia de Configuração e Testes**](./GUIA_CONFIGURACAO.md#🧪-guia-de-testes-mvp).

Para testar o fluxo de "esqueci minha senha" em uma instalação local já existente, recrie o volume do Keycloak para reimportar o realm com SMTP configurado:

```bash
docker compose down -v
docker compose up -d --build
```
