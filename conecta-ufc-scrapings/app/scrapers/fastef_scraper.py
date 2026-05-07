from bs4 import BeautifulSoup
from app.scrapers.base_scraper import BaseScraper


class FastefScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.url = "https://fastef.ufc.br/processos-seletivos/"
        self.origem = "FASTEF"

    def run(self):
        """Método principal que orquestra a raspagem."""
        self.logger.info(f"Iniciando requisição para: {self.url}")
        html_content = self.fetch_html(self.url)

        if not html_content:
            self.logger.error("Falha ao obter o HTML da FASTEF. Abortando extração.")
            return []

        return self.parse_html(html_content)

    def parse_html(self, html_content):
        self.logger.info("Iniciando o parsing do HTML da FASTEF...")
        soup = BeautifulSoup(html_content, 'lxml')
        oportunidades = []

        cartoes = soup.find_all('div', class_='vc_grid-item')

        for cartao in cartoes:
            tag_titulo = cartao.find('h4')
            titulo = tag_titulo.get_text(strip=True) if tag_titulo else "Sem Título"

            tag_link = cartao.find('a', class_='vc_btn3')
            if not tag_link:
                tag_link = cartao.find('a', class_='vc_gitem-link')

            link = tag_link.get('href') if tag_link else None

            if link and titulo != "Sem Título":
                vaga = {
                    "titulo": titulo,
                    "origem": self.origem,
                    "tipo": "Processo Seletivo",
                    "link": link
                }
                oportunidades.append(vaga)

        self.logger.info(f"Total de itens extraídos: {len(oportunidades)}")
        return oportunidades