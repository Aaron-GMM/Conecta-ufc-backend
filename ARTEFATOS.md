# Apresentação dos Artefatos - Conecta-UFC

Este documento descreve os artefatos produzidos pela equipe durante o desenvolvimento do projeto **Conecta-UFC**.

## 1. Protótipo de Alta Fidelidade (UI/UX)
O design da interface foi elaborado no Figma, focando na usabilidade e na centralização das informações de editais.
*   **Link do Figma:** [Conecta-UFC Design](https://www.figma.com/design/81oE8ByfTje6hoOWlzrSoI/Conecta-UFC?node-id=0-1&p=f&t=Ou7BDXSjktoAt3Ej-0)

## 2. Ecossistema de Backend e Coleta
O sistema foi dividido em dois componentes principais seguindo a arquitetura *Store and Forward*.

### 2.1. Core Backend (`conecta-ufc-backend`)
*   **Tecnologia:** FastAPI (Python 3.12).
*   **Persistência:** PostgreSQL.
*   **Autenticação:** Integrada com **Keycloak** via OpenID Connect.
*   **Funcionalidades:** Gerenciamento de usuários, sistema de favoritos, ingestão de dados via API Key e exposição de oportunidades normalizadas.

### 2.2. Worker Scraper (`conecta-ufc-scrapings`)
*   **Tecnologia:** BeautifulSoup4, HTTPX e Regex.
*   **Persistência Local:** SQLite (Staging Area).
*   **Diferencial Técnico:** Implementação do **Algoritmo Two-Pass** e padrão **Ghost Parent** para garantir integridade referencial entre editais e resultados, mesmo quando os dados de origem estão desorganizados.
*   **Parsers:** Scrapers específicos para UFC Quixadá e FASTEF.

## 3. Banco de Dados
*   **Diagrama Entidade-Relacionamento (DER):** Modelagem completa incluindo tabelas de `oportunidades`, `resultados`, `usuarios`, `favoritos` e `alertas`.
*   **Migrações:** Gerenciadas via **Alembic**, garantindo versionamento do esquema tanto no SQLite quanto no PostgreSQL.

## 4. Documentação Técnica
*   **[Documento de Arquitetura](./ARQUITETURA.md):** Detalhamento das decisões de design, motivações tecnológicas e diagramas Mermaid.
*   **[Auditoria e Planejamento](./RELATORIO_PLANEJAMENTO.md):** Mapeamento de requisitos, estado atual do projeto e cronograma de sprints.
*   **[Guia de Integração Auth](./GUIA_AUTH.md):** Manual técnico detalhando a integração com Keycloak e fluxos de autenticação.

## 5. Infraestrutura e DevOps
*   **Containerização:** Arquivos `Dockerfile` e `docker-compose.yml` para orquestração do banco de dados, Keycloak e serviços da aplicação.
*   **Gerenciamento de Dependências:** Uso de `uv` e `pip` para garantir ambientes reprodutíveis.
