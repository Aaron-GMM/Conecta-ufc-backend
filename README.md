Entendido. Vamos elevar o tom técnico e eliminar as metáforas informais. O foco aqui é transparecer a robustez da arquitetura distribuída e a seriedade do projeto acadêmico.

Aqui está a versão refinada do **README.md** central, projetada para servir tanto como guia para desenvolvedores humanos quanto como "fonte da verdade" para assistentes de IA:

---

# Conecta-UFC: Sistema Distribuído de Agregação de Oportunidades

O **Conecta-UFC** é uma plataforma de alta disponibilidade projetada para centralizar e normalizar a oferta de oportunidades acadêmicas e profissionais (bolsas de fomento, monitorias, extensões e editais de pesquisa) da Universidade Federal do Ceará. 

O ecossistema opera sob o padrão **Store and Forward**, desacoplando a fase crítica de extração de dados (*Edge Data Collection*) da camada de entrega e serviços (*Centralized API*).

---

## 📂 Documentação Técnica e Diagramas

Para uma compreensão aprofundada dos subsistemas, consulte:

* **[Arquitetura e Contexto de Negócio](./Doc-Conecta-UFC.md):** Visão macro do sistema e decisões de design.
* **[Diagramas e Fluxos de Dados](./Diagramas.md):** Visualização via Mermaid do DER, Camadas, Algoritmo de Scraping e Sequência.

---

## 🏗️ Arquitetura do Ecossistema

O repositório é segmentado em dois componentes independentes, permitindo escalabilidade vertical e horizontal conforme a demanda:

### 1. Serviço de Coleta (`conecta-ufc-scrapings`)
* **Função:** Engine de extração assíncrona baseada em BeautifulSoup4 e HTTPX.
* **Persistência de Staging:** Utiliza **SQLite** para garantir que a coleta não seja interrompida por instabilidades na rede externa ou indisponibilidade momentânea do Core.
* **Inteligência de Vínculo:** Implementa o algoritmo **Two-Pass** com lógica de **Ghost Parent** para manter a integridade referencial entre Editais e seus respectivos Resultados.

### 2. Núcleo de Processamento (`conecta-ufc-backend`)
* **Função:** API RESTful de alta performance desenvolvida em **FastAPI**.
* **Cofre de Dados:** Persistência definitiva em **PostgreSQL** com migrações gerenciadas via **Alembic**.
* **Segurança:** Ingestão de dados protegida por API Key e entrega para o frontend otimizada via Pydantic Schemas.

---

## 🛠️ Stack Tecnológica

| Tecnologia | Finalidade |
| :--- | :--- |
| **Python 3.12** | Core Language (Gerenciamento com `uv`) |
| **FastAPI** | Framework Web Assíncrono |
| **SQLAlchemy** | Mapeamento Objeto-Relacional (ORM) |
| **PostgreSQL** | Banco de Dados de Produção (Relacional) |
| **Pydantic** | Validação de Dados e Higienização (Type Hinting) |



---
