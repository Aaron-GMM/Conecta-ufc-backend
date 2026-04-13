## 🚀 Plano de Ação: Implementação dos Scrapers

### Fase 1: Mapeamento e Estudo de Alvos
* **Identificação de Seletores:** Inspecionar o HTML dos sites (FASTEF, Insight, UFC) para identificar IDs e Classes CSS das listas de vagas.
* **Tratamento de Paginação:** Verificar se o site carrega as vagas via scroll infinito, botões "Próximo" ou se estão todas em uma página só.
* **Identificação de Padrões:** Mapear onde fica o link do edital, o título e a data de encerramento em cada fonte.

### Fase 2: Desenvolvimento do Core (Python ou TS)
* **Normalizador de Dados:** Criar uma função que recebe o dado bruto do site e transforma em um objeto padrão:
    ```json
    { "titulo": "Monitoria PID", "origem": "UFC", "tipo": "Graduação", "link": "..." }
    ```
* **Tratamento de Erros:** Implementar blocos `try-catch` para que, se um site mudar o layout, o scraper dos outros sites continue funcionando.
* **Deduplicação:** Lógica para não inserir a mesma vaga duas vezes no banco de dados a cada execução.

### Fase 3: Automação e Persistência
* **Integração com BD:** Conectar o script ao banco (ex: Supabase ou MongoDB Atlas).
* **Agendamento (Cron Job):** Configurar o script para rodar automaticamente (ex: a cada 12 ou 24 horas).

---

## 🛠️ Sugestões de Hosting (Gratuitos/Freemium)

Hospedar scrapers exige que o servidor permita processos em segundo plano ou tarefas agendadas.

| Plataforma | Melhor para... | Vantagem |
| :--- | :--- | :--- |
| **Render** | Backend e Scrapers | Plano grátis robusto para Python/Node. Fácil deploy via GitHub. |
| **Railway** | Banco de Dados e App | Muito simples de usar, oferece um crédito fixo mensal no plano trial. |
| **GitHub Actions** | Executar o Scraper | Você pode agendar o script para rodar **dentro** do GitHub e salvar os dados no BD. **(Altamente recomendado para o seu caso)**. |
| **Supabase** | Banco de Dados | Melhor alternativa ao Firebase. PostgreSQL grátis e muito rápido para configurar. |
| **Vercel** | Frontend (React/TS) | O padrão ouro para hospedar o site que o aluno vai acessar. |

---

## 💡 Sugestão de Stack para "Easy Deploy"

Para garantir que o projeto fique no ar sem custos e com zero manutenção manual:

1.  **Linguagem:** **Python** (pela facilidade com bibliotecas de scraping e manipulação de strings).
2.  **Scraper:** **BeautifulSoup4** (mais leve que Selenium e roda fácil em qualquer servidor).
3.  **Execução do Scraper:** **GitHub Actions**. Crie um arquivo `.yml` que roda seu script todo dia às 08:00 e envia os dados para o banco.
4.  **Banco de Dados:** **Supabase** (PostgreSQL).
5.  **Frontend:** **React** ou **Next.js** hospedado na **Vercel**.

---

## 📝 Próximos Passos (Backlog)

1.  **Finalizar a Engenharia de Requisitos:** (Funcionais, Não Funcionais e Regras de Negócio).
2.  **Modelagem do Banco:** Definir a tabela de `Vagas` e `Usuarios_Admin`.
3.  **Prototipagem:** Desenhar a tela de listagem para validar com alguns alunos (stakeholders).

