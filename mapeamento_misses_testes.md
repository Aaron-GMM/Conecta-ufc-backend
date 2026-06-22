# Mapeamento de Misses (Falhas de Cobertura) nos Testes

Abaixo estão detalhados todos os "misses" (linhas não cobertas pelos testes) levantados pelos relatórios do **Backend** e do serviço de **Scrapings**, acompanhados das respectivas propostas de solução para alcançarmos 100% de cobertura.

---

## 1. Módulo: Backend

### `app/core/auth.py`
- **Onde/O que é:** Linhas 16, 28, 61. Relacionado ao *fallback* de inicialização e exceções gravíssimas e raras de decodificação JWT (simulação de Token forjado).
- **Proposta de Solução:** Criar um teste unitário que use o pacote `pytest-mock` para injetar uma exceção (`side_effect=Exception`) forçando o erro de decodificação `JWTError` no exato ponto em que o token é lido. Para a linha 16, pode-se simular a ausência de variáveis de ambiente.

### `app/db/database.py`
- **Onde/O que é:** Linhas 9, 17-21. Levanta `ValueError` quando `DATABASE_URL` não existe no ambiente, além da inicialização de drivers de PostgreSQL de produção que são pulados no E2E (usando SQLite no E2E ao invés de Postgre).
- **Proposta de Solução:** Escrever um teste unitário (`test_database.py`) onde limpamos a variável global `DATABASE_URL` usando `monkeypatch.delenv("DATABASE_URL")` e instanciamos o DB para capturar a exceção esperada via `pytest.raises`.

### `app/schemas/favorito.py`
- **Onde/O que é:** Linhas 1-12. É apontado com 0% no E2E porque os construtores de pydantic lá dentro nunca são evocados. A API utiliza IDs primitivos na rota.
- **Proposta de Solução:** O schema tornou-se residual no código. A solução definitiva e mais correta é **remover o arquivo `favorito.py`** (ou as linhas não usadas) já que o código do projeto não depende dele de fato, limpando a base de dados de código morto.

### `app/services/data_quality.py`
- **Onde/O que é:** Linhas 11, 15, 20, 55-56. Capturas de Timeout na requisição HTTP que checa se o link do PDF é acessível ou está quebrado.
- **Proposta de Solução:** Adicionar um teste unitário específico no backend usando `requests-mock` ou `responses` configurado para disparar um `requests.exceptions.Timeout` quando a URL for acessada, validando o bloco de `except Timeout:`.

### `app/services/keycloak_service.py`
- **Onde/O que é:** Linhas 17, 69-70, 119-121. Respostas catastróficas como *Internal Server Error* do servidor Keycloak.
- **Proposta de Solução:** Injetar um mock (`patch`) em cima do objeto que realiza o Request pro Keycloak para retornar um objeto com `status_code = 500`. 

### `app/services/oportunidade_service.py`
- **Onde/O que é:** Linhas 37-38. Condição muito rara de falha na iteração do relacionamento reverso SQL `resultados`.
- **Proposta de Solução:** Simular um teste unitário com um mock no objeto SQL retornando `None` ou quebrando (`side_effect=AttributeError`) na hora em que for iterar os resultados de uma oportunidade mockada.

### `app/api/routes/internal.py`
- **Onde/O que é:** Linhas 65-73. Branch de validação de estrutura extra do modelo Pydantic que não se aplica nas lógicas de inserção já mockadas.
- **Proposta de Solução:** Enviar propositalmente, num teste de integração, um Payload pela rota `POST /internal/sync` formatado incorretamente de uma forma muito específica para acionar esse bloco, garantindo que o exception seja acionado e devolva `422 Unprocessable Entity` ou erro mapeado.

---

## 2. Módulo: Scrapings

### `app/db/database.py`
- **Onde/O que é:** Linhas 30-34. Linhas de erro crasso de conexão com banco de dados não encontradas (falha de Driver).
- **Proposta de Solução:** Da mesma forma que no Backend, no diretório de testes de banco, criar um caso unitário que use `monkeypatch` alterando o ambiente para uma string de conexão `sqlite:///invalida` e esperar pelo bloco `except Exception as e:` que inicializa o logger de erro de banco.

### `app/scrapers/fastef_scraper.py`
- **Onde/O que é:** Linha 37. Bloco defensivo de *fallback* para links de editais sem tag `<a>`.
- **Proposta de Solução:** Passar para a função interna de *parseamento* de HTML do FASTEF uma string HTML customizada e "quebrada" onde o link não seja clicável (sem `<a>`), forçando a execução da condicional `if not tag_a:`.

### `app/scrapers/pdf_parser.py`
- **Onde/O que é:** Cerca de 13 linhas de exceptions para PDFs impossíveis de ler (`ValueError` em datas não-padrão ou arrays curtos do pdfplumber devido a páginas vazias).
- **Proposta de Solução:** Incluir amostras de PDF forjados e mal-formatados dentro da pasta `tests/amostras_pdf` (Ex: um PDF de 1 página em branco sem texto algum, e um com datas no formato `abril, 20`). Alimentar esses PDFs diretamente na classe de testes unitários para passar pelas frentes dos blocos `except`.

### `app/scrapers/ufc_scraper.py`
- **Onde/O que é:** Linhas 45-46, 62-63. Falhas invisíveis no Try/Except de processamento do Regex de captura de Datas de fim e de início.
- **Proposta de Solução:** Mockar a resposta da URL local com um HTML (`requests-mock`) no qual o conteúdo textual da vaga use um formato não identificado (ex: `Período: até durar` ou data omissa) para acionar os blocos de exceção controlada no parse.
