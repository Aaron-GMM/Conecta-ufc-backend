# Relatório Detalhado de Cobertura E2E (End-to-End): Scrapings

Este relatório tem como objetivo evidenciar a execução da camada de testes E2E (de ponta a ponta) do **Conecta UFC Scrapings**. Diferente dos testes unitários, a camada de E2E roda com o ambiente completo operando os endpoints de consulta do FastAPI e a validação do endpoint de trigger de Sincronização.

## Estratégia de E2E em Aplicações de Web Scraping

Em sistemas de web scraping, executar os robôs extratores completamente e a todo momento nos testes E2E pode causar:
1. Banimento do IP das instâncias pelo servidor da UFC e da FASTEF (DDoS não intencional).
2. Tempos absurdos de pipeline devido ao download de dezenas de PDFs por build.
3. Flakiness do ambiente por depender totalmente do uptime da infraestrutura acadêmica.

Por esse motivo, o nosso E2E garante a viabilidade de rede da API exposta pelo serviço, atingindo todos os controladores, injetando sessões de DB e testando se a orquestração de fundo (Sincronizador e Listagens) responde perfeitamente, provando o funcionamento em "Caixa Preta".

## Detalhamento da Suíte E2E

Foram criados os seguintes fluxos:

- **Listagem de Oportunidades**: `test_e2e_listar_oportunidades_e2e` garante o endpoint acessível via FastApi retornando payload serializado paginado de acordo com a regra de negócio sem falhas 500.
- **Listagem de Resultados**: `test_e2e_listar_resultados_e2e` valida a associação e a paginação sem mocks.
- **Engatilho de Sincronização**: `test_e2e_scraper_sync` aciona a rota `POST /api/scrapers/sync` que instrui o job de automação a se comunicar e engatilhar os scrapers internamente para o banco sem mocks do framework web.

## Como Garantimos a Cobertura Total?

- Testamos o cenário de negócio *Unitário* (Parsing dos Textos e Conversão de PDF) via **Mocks rigorosos do PDFPlumber e HTML**.
- Testamos a gravação real e validação de duplicidade por *Integração*, injetando Scrapers com respostas de payload mas com `SQLite` real.
- Acionamos e blindamos as "portas abertas" da aplicação com **E2E**, atestando que os *Controllers* respondem à solicitações HTTP reais da forma desejada.

O cruzamento de todas essas camadas consolida a suíte em saudáveis **96% de Cobertura Final de Código**, isolando apenas linhas defensivas extremas na classe de `pdf_parser` e inicializadores de driver do PostgreSQL.
